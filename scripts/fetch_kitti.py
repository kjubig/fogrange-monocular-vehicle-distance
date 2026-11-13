"""Download a part of KITTI 3D Object into data/kitti/.

The official archives are large (images 12 GB, lidar 29 GB). They are zip files on a server that lets
us read any part of a file, so we read each archive's table of contents and then only the frames we
want. Labels and calibration are small and are downloaded whole.

Only the `training` part of KITTI has labels, so it is split in two with the lists most papers use
(3712 train and 3769 val frames, taken from different recordings):
    train  for tuning the methods,
    val    only for the final numbers.

Run from the repository root; the number is how many frames to fetch, half from each list:
    .venv/bin/python scripts/fetch_kitti.py 200
Running it again with a bigger number adds frames and keeps the ones already there.
"""

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

OUT = Path("data/kitti")
KITTI = "https://s3.eu-central-1.amazonaws.com/avg-kitti"  # The server behind the download links on cvlibs.net.
SPLIT = "https://raw.githubusercontent.com/open-mmlab/OpenPCDet/master/data/kitti/ImageSets"


class RemoteFile(io.RawIOBase):
    """A file on a server, read piece by piece, so that zipfile can open an archive without downloading it."""

    def __init__(self, url):
        self.url, self.position = url, 0
        head = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"))
        self.size = int(head.headers["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        start = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence]
        self.position = start + offset
        return self.position

    def readinto(self, buffer):
        last = min(self.position + len(buffer), self.size) - 1
        if last < self.position:
            return 0
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={self.position}-{last}"})
        data = urllib.request.urlopen(request).read()
        buffer[: len(data)] = data
        self.position += len(data)
        return len(data)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Which frames: the first count/2 of each list. KITTI numbered its frames in random order, so
    #    the first frames of a list are a random sample of recordings.
    frames = []
    for part in ("train", "val"):
        with urllib.request.urlopen(f"{SPLIT}/{part}.txt") as response:
            chosen = response.read().decode().split()[: count // 2]
        (OUT / f"{part}.txt").write_text("\n".join(chosen) + "\n")
        frames += chosen

    # 2. Labels (5 MB) and calibration (26 MB): whole archives, but only their `training` folder.
    for name, folder in (("data_object_label_2", "label_2"), ("data_object_calib", "calib")):
        if not (OUT / "training" / folder).exists():
            print("downloading", name)
            with urllib.request.urlopen(f"{KITTI}/{name}.zip") as response:
                archive = zipfile.ZipFile(io.BytesIO(response.read()))
            archive.extractall(OUT, [member for member in archive.namelist() if member.startswith("training/")])

    # 3. Images and lidar: only the chosen frames, read straight out of the remote archives.
    for name, folder, extension in (("data_object_image_2", "image_2", "png"), ("data_object_velodyne", "velodyne", "bin")):
        (OUT / "training" / folder).mkdir(parents=True, exist_ok=True)
        missing = [frame for frame in frames if not (OUT / "training" / folder / f"{frame}.{extension}").exists()]
        if missing:
            archive = zipfile.ZipFile(io.BufferedReader(RemoteFile(f"{KITTI}/{name}.zip"), buffer_size=1 << 16))
        for number, frame in enumerate(missing, start=1):
            member = f"training/{folder}/{frame}.{extension}"
            (OUT / member).write_bytes(archive.read(member))
            if number % 20 == 0 or number == len(missing):
                print(f"{folder}: {number}/{len(missing)}")
    print(f"Done: {len(frames)} frames in {OUT}/training, frame lists in {OUT}/train.txt and {OUT}/val.txt")


if __name__ == "__main__":
    main()
