"""Check the KITTI frames fetched by scripts/fetch_kitti.py before any method runs on them.

1. Every frame: the image opens, the lidar file is whole, calibration and labels can be read.
2. Do image, lidar, calibration and labels belong together? For every fully visible labelled vehicle,
   the lidar points that fall into the centre of its 2D box should lie at the distance of its 3D box.
3. A picture of 5 random frames to look at: lidar points coloured by depth (near red, far blue) and
   the labelled boxes with their distances.

Run from the repository root:
    .venv/bin/python scripts/check_kitti.py
"""

import random
from pathlib import Path

import cv2
import numpy as np
from three_methods import draw, m3_lidar, nearest_face, read_kitti_calib, read_lidar, read_rgb

DATA = Path("data/kitti")
OUT = Path("results/kitti")


def load(frame):
    """One frame of data/kitti: image, projection matrix P, lidar points in the camera frame, labelled vehicles."""
    folder = DATA / "training"
    P, lidar_to_camera = read_kitti_calib(folder / "calib" / f"{frame}.txt")
    labels = []
    for line in open(folder / "label_2" / f"{frame}.txt"):
        f = line.split()  # type, truncated, occluded, alpha, box 2D (4), h w l, x y z, rotation_y
        if f[0] in ("Car", "Van", "Truck"):
            width, length, z, yaw = float(f[9]), float(f[10]), float(f[13]), float(f[14])
            labels.append(dict(box=np.array(f[4:8], dtype=float), distance=nearest_face(z, length, width, yaw),
                               fully_visible=float(f[1]) == 0 and int(f[2]) == 0))
    points = read_lidar(folder / "velodyne" / f"{frame}.bin", 4, lidar_to_camera)  # Fails if the file is cut short.
    return dict(image=read_rgb(folder / "image_2" / f"{frame}.png"), P=P, points=points, labels=labels)


def main():
    frames = (DATA / "train.txt").read_text().split() + (DATA / "val.txt").read_text().split()

    # 1 and 2. Read every frame and compare the lidar with the labels.
    broken, differences = [], []  # differences: (lidar distance - label distance, frame)
    for frame in frames:
        try:
            sample = load(frame)
        except Exception as error:
            broken.append((frame, error))
            continue
        for label in sample["labels"]:
            lidar, count = m3_lidar(label["box"], sample["points"], sample["P"])
            if label["fully_visible"] and count >= 10:
                differences.append((lidar - label["distance"], frame))
    print(f"{len(frames)} frames, {len(broken)} could not be read")
    for frame, error in broken:
        print("  ", frame, error)
    gaps = np.abs([difference for difference, _ in differences])
    print(f"{len(gaps)} fully visible vehicles with at least 10 lidar points in the centre of the box:")
    print(f"   lidar and label differ by {np.median(gaps):.2f} m (median); {100 * np.mean(gaps < 1):.0f}% within 1 m")
    print("   largest differences:", ", ".join(f"{d:+.1f} m in {frame}" for d, frame in sorted(differences, key=lambda x: -abs(x[0]))[:5]))

    # 3. Five random frames to look at.
    rows = []
    for frame in random.Random(0).sample(frames, 5):
        sample = load(frame)
        canvas = draw(sample["image"], [], sample["points"], sample["P"])
        for label in sample["labels"]:
            x1, y1, x2, y2 = label["box"].astype(int)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(canvas, f"{label['distance']:.1f} m", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(canvas, frame, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
        rows.append(cv2.resize(canvas, (1242, 375)))  # KITTI images differ by a few pixels in size.
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / "check.png"), cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR))
    print(f"Picture of 5 random frames saved to {OUT / 'check.png'}")


if __name__ == "__main__":
    main()
