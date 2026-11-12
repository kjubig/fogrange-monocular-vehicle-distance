"""Download one good-weather and one bad-weather frame per dataset into data/one_frame/.

KITTI       frame 000007 from a public repository that ships a few KITTI frames (image, lidar,
            calibration, labels). The full dataset needs registration at cvlibs.net.
            KITTI is good weather only.
STF        the example frame of the official SeeingThroughFog repository (image and lidar, no
            labels), split train_clear_day.
STF snow    another example frame of that repository (image only), split snow_day.
SHIFT       official servers are down, so frames are read from an unofficial mirror on Hugging
            Face: image, 3D labels and the simulator depth map. The mirror has no lidar.
"""

import csv
import io
import json
import shutil
import struct
import tempfile
import urllib.request
from pathlib import Path

import cv2

OUT = Path("data/one_frame")
KITTI = "https://raw.githubusercontent.com/ghimiredhikura/Complex-YOLOv3/master/data/KITTI/object/sampledata"
STF = "https://raw.githubusercontent.com/princeton-computational-imaging/SeeingThroughFog/master/tools"
SHIFT = "https://huggingface.co/datasets/KevinConnorLee/SHIFT/resolve/main"


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(url, path)


def read_range(url: str, start: int, length: int) -> bytes:
    """Read part of a remote file, so huge archives never have to be downloaded."""
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{start + length - 1}"})
    with urllib.request.urlopen(request) as response:
        return response.read()


def fetch_shift(folder_name: str, weather: str) -> None:
    folder = OUT / folder_name
    if (folder / "depth.png").exists():
        return
    base = f"{SHIFT}/discrete/videos/train/front"

    # 1. Daytime sequences with this weather, in the (alphabetical) order of the label file.
    with urllib.request.urlopen(f"{base}/seq.csv") as response:
        rows = list(csv.DictReader(io.StringIO(response.read().decode())))
    candidates = [
        row["video"]
        for row in rows[:100]
        if row["start_weather_fine"] == weather and row["start_timeofday_fine"] in ("noon", "morning/afternoon")
    ]

    # 2. img.tar holds one mp4 per sequence: walk the tar headers until a candidate turns up.
    offset = 0
    while True:
        header = read_range(f"{base}/img.tar", offset, 512)
        name = header[:100].split(b"\0")[0].decode().removeprefix("./").removesuffix(".mp4")
        size = int(header[124:136].strip(b"\0 ") or b"0", 8)
        if name in candidates:
            video = read_range(f"{base}/img.tar", offset + 512, size)
            break
        print("  skipping", name)
        offset += 512 + (size + 511) // 512 * 512
    sequence = name
    print("SHIFT sequence:", sequence)

    # 3. Labels: stream the label file (6.5 GB) only until this sequence has been read.
    frames, buffer, position, decoder = [], "", 0, json.JSONDecoder()
    with urllib.request.urlopen(f"{base}/det_3d.json") as response:
        buffer = response.read(1 << 20).decode()
        position = buffer.index("[") + 1
        while True:
            position = len(buffer) - len(buffer[position:].lstrip(", \n"))
            try:
                frame, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                buffer = buffer[position:] + response.read(1 << 20).decode()
                position = 0
                continue
            position = end
            if frame["videoName"] == sequence:
                frames.append(frame)
            elif frame["videoName"] > sequence:
                break

    # The frame with the most vehicles closer than 80 m, sampled at 1 frame per second.
    def vehicles(frame):
        labels = frame.get("labels") or []
        return [lab for lab in labels if lab["category"] in ("car", "truck", "bus") and "box3d" in lab and lab["box3d"]["location"][2] < 80]

    frame = max(frames[::10], key=lambda frame: len(vehicles(frame)))
    index = frame["frameIndex"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "labels.json").write_text(json.dumps(frame, indent=1))

    # 4. Image: frame number `index` of the sequence video.
    with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
        handle.write(video)
        handle.flush()
        capture = cv2.VideoCapture(handle.name)
        for _ in range(index + 1):  # Read frame by frame: seeking in mp4 can land on the wrong frame.
            ok, image = capture.read()
    cv2.imwrite(str(folder / "image.png"), image)

    # 5. Depth: one PNG from a 722 GB ZIP split into six parts. Its directory sits at the end of the last part.
    parts = [f"{SHIFT}/depth.part.a{letter}" for letter in "abcdef"]
    sizes = [int(urllib.request.urlopen(urllib.request.Request(part, method="HEAD")).headers["Content-Length"]) for part in parts]

    def read_archive(start: int, length: int) -> bytes:
        data = b""
        for part, size in zip(parts, sizes):
            if start < size and length > 0:
                chunk = read_range(part, start, min(length, size - start))
                data, length, start = data + chunk, length - len(chunk), 0
            else:
                start -= size
        return data

    total = sum(sizes)
    tail = read_archive(total - 65536, 65536)
    record = tail[tail.rfind(b"PK\x06\x06") :]  # ZIP64 end of central directory.
    directory_size, directory_offset = struct.unpack_from("<QQ", record, 40)
    directory = read_archive(directory_offset, directory_size)
    wanted = f"{sequence}/{index:08d}_depth_front.png".encode()
    at = directory.index(wanted) - 46  # Start of this file's directory record.
    assert struct.unpack_from("<H", directory, at + 10)[0] == 0, "expected an uncompressed (stored) file"
    stored_size = struct.unpack_from("<I", directory, at + 20)[0]
    name_length, extra_length = struct.unpack_from("<HH", directory, at + 28)
    extra = directory[at + 46 + name_length : at + 46 + name_length + extra_length]
    local_offset = struct.unpack_from("<Q", extra, 4)[0]  # ZIP64 extra field: the 64-bit offset.
    local = read_archive(local_offset, 30)
    data_start = local_offset + 30 + sum(struct.unpack_from("<HH", local, 26))
    (folder / "depth.png").write_bytes(read_archive(data_start, stored_size))
    print(f"SHIFT frame {index} with {len(vehicles(frame))} vehicles")


def main() -> None:
    for folder, local in (("image_2", "image.png"), ("velodyne", "lidar.bin"), ("calib", "calib.txt"), ("label_2", "label.txt")):
        download(f"{KITTI}/{folder}/000007.{local.split('.')[1]}", OUT / "kitti" / local)
    download(f"{STF}/DatasetFoggification/example_data/ImageData/2019-09-11_19-13-44_00960.png", OUT / "stf" / "image.png")
    download(f"{STF}/DatasetFoggification/example_data/LidarData/2019-09-11_19-13-44_00960.bin", OUT / "stf" / "lidar.bin")
    # The authors' calibration of the left camera and the HDL-64 lidar, written in the KITTI format.
    download(f"{STF}/ProjectionTools/Sweden2KittiCalib/kitti_stereo_velodynehdl_calib.txt", OUT / "stf" / "calib.txt")
    fetch_shift("shift", "clear")

    # Bad weather (KITTI has none).
    download(f"{STF}/Raw2LUTImages/example_data/cam_stereo_left_lut/2018-02-12_15-39-23_00100.png", OUT / "stf_snow" / "image.png")
    shutil.copy(OUT / "stf" / "calib.txt", OUT / "stf_snow" / "calib.txt")
    fetch_shift("shift_fog", "heavy fog")
    print("Done:", sorted(str(path) for path in OUT.rglob("*.*")))


if __name__ == "__main__":
    main()
