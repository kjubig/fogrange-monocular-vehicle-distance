"""Distance to the cars in KITTI, Seeing Through Fog and SHIFT frames, good and bad weather, measured three ways.

Every method starts from the same YOLO box around a car:
  M1 geometry       road:   Z = f * H_camera / (y_bottom - y_horizon)   (flat road, level camera)
                    height: Z = f * h_car / h_box                       (typical height of the class)
  M2 depth network  median of the Depth Anything V2 Metric depth map in the centre of the box
  M3 lidar          median depth of the lidar points that fall into the centre of the box
  GT                distance to the nearest face of the labelled 3D box (KITTI and SHIFT only)

Run from the repository root, after scripts/fetch_samples.py:
    .venv/bin/python scripts/three_methods.py
"""

import csv
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import pipeline
from ultralytics import YOLO

DATA = Path("data/one_frame")
OUT = Path("results/one_frame")
DEPTH_MODEL = "depth-anything/Depth-Anything-V2-Metric-Outdoor-Small-hf"
CLASS_HEIGHT = {"car": 1.52, "truck": 2.6, "bus": 3.2}  # Metres. Car and truck: means of KITTI training labels.
CENTRE = 0.4  # M2 and M3 use the central 40% of the box: less road, background and neighbouring cars.
DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"


# --- Loading one frame: image, projection matrix P (3x4), camera height, lidar points, labels ----------


def read_rgb(path):
    return cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)


def read_kitti_calib(path):
    """Camera projection P2 (3x4) and the transform from lidar to camera (3x4), KITTI file format."""
    values = {}
    for line in open(path):
        if ":" in line:
            key, numbers = line.split(":", 1)
            values[key] = np.array(numbers.split(), dtype=float)
    lidar_to_camera = values["R0_rect"].reshape(3, 3) @ values["Tr_velo_to_cam"][:12].reshape(3, 4)
    return values["P2"].reshape(3, 4), lidar_to_camera


def read_lidar(path, columns, lidar_to_camera):
    """Lidar points in the camera frame: x right, y down, z forward (metres)."""
    xyz = np.fromfile(path, dtype=np.float32).reshape(-1, columns)[:, :3]
    return xyz @ lidar_to_camera[:, :3].T + lidar_to_camera[:, 3]


def nearest_face(z, length, width, yaw):
    """Distance along the camera axis to the nearest face of a 3D box whose centre is at depth z."""
    return z - abs(np.sin(yaw)) * length / 2 - abs(np.cos(yaw)) * width / 2


def load_kitti(folder):
    P, lidar_to_camera = read_kitti_calib(folder / "calib.txt")
    labels = []  # (2D box, ground-truth distance)
    for line in open(folder / "label.txt"):
        f = line.split()  # type, truncated, occluded, alpha, box 2D (4), h w l, x y z, rotation_y
        if f[0] in ("Car", "Van", "Truck"):
            width, length, z, yaw = float(f[9]), float(f[10]), float(f[13]), float(f[14])
            labels.append((np.array(f[4:8], dtype=float), nearest_face(z, length, width, yaw)))
    points = read_lidar(folder / "lidar.bin", 4, lidar_to_camera)  # x, y, z, reflectance
    # Camera height 1.65 m above the road: Geiger et al., IJRR 2013, Fig. 3.
    return dict(image=read_rgb(folder / "image.png"), P=P, camera_height=1.65, points=points, labels=labels)


def load_stf(folder):
    P, lidar_to_camera = read_kitti_calib(folder / "calib.txt")
    image = read_rgb(folder / "image.png")
    if image.shape[1] == 1792:  # The good-weather example is the full 1920x1024 frame cropped at x=84, y=200,
        P[0, 2] -= 84  # found by matching the lidar to the depth map published with that image.
        P[1, 2] -= 200
    points = None
    if (folder / "lidar.bin").exists():
        points = read_lidar(folder / "lidar.bin", 5, lidar_to_camera)  # x, y, z, intensity, laser ring
    # Camera height from the dataset's sensor tree (0.35 m + 0.89 m); no labels are public for these frames.
    return dict(image=image, P=P, camera_height=1.24, points=points, labels=[])


def load_shift(folder):
    frame = json.loads((folder / "labels.json").read_text())
    (fx, fy), (cx, cy) = frame["intrinsics"]["focal"], frame["intrinsics"]["center"]
    labels = []
    for label in frame["labels"]:
        if label["category"] in ("car", "truck", "bus"):
            box, box3d = label["box2d"], label["box3d"]  # location: box centre; dimension: h, w, l
            _, width, length = box3d["dimension"]
            distance = nearest_face(box3d["location"][2], length, width, box3d["orientation"][1])
            labels.append((np.array([box["x1"], box["y1"], box["x2"], box["y2"]]), distance))
    bgr = cv2.imread(str(folder / "depth.png")).astype(float)  # Simulator depth: 24 bits over 1000 m.
    depth = (bgr[..., 2] + 256 * bgr[..., 1] + 65536 * bgr[..., 0]) / 2**24 * 1000
    P = np.array([[fx, 0, cx, 0], [0, fy, cy, 0], [0, 0, 1, 0]], dtype=float)
    # Camera height above the world origin; the road of this flat town lies at height 0.
    camera_height = frame["extrinsics"]["location"][2]
    # The mirror has no lidar, but the simulator's depth map is exact: it is what fine-tuning learns from.
    note = f"{frame['attributes']['weather_fine']}, {frame['attributes']['timeofday_fine']}"
    return dict(image=read_rgb(folder / "image.png"), P=P, camera_height=camera_height, points=None, labels=labels,
                depth_gt=depth, note=note)


# --- The three methods. Each gets one YOLO box -----------------------------------------------------------


def m1_road(box, P, camera_height):
    """The bottom edge of the box touches a flat road; the horizon is the image row of the optical axis."""
    f, y_horizon = P[1, 1], P[1, 2]
    return f * camera_height / (box[3] - y_horizon) if box[3] > y_horizon else np.nan


def m1_height(box, P, cls):
    """A car of known height h appears h_box pixels tall."""
    return P[1, 1] * CLASS_HEIGHT[cls] / (box[3] - box[1])


def centre(box):
    x1, y1, x2, y2 = box
    half_w, half_h = CENTRE * (x2 - x1) / 2, CENTRE * (y2 - y1) / 2
    return (x1 + x2) / 2 - half_w, (y1 + y2) / 2 - half_h, (x1 + x2) / 2 + half_w, (y1 + y2) / 2 + half_h


def m2_network(box, depth):
    x1, y1, x2, y2 = (int(round(value)) for value in centre(box))
    return float(np.median(depth[y1 : y2 + 1, x1 : x2 + 1]))


def m3_lidar(box, points, P):
    """Median depth of the lidar points projected into the centre of the box."""
    ahead = points[points[:, 2] > 1.0]
    uvw = ahead @ P[:, :3].T + P[:, 3]
    u, v = uvw[:, 0] / uvw[:, 2], uvw[:, 1] / uvw[:, 2]
    x1, y1, x2, y2 = centre(box)
    inside = (u > x1) & (u < x2) & (v > y1) & (v < y2)
    return (float(np.median(ahead[inside, 2])) if inside.sum() >= 3 else np.nan), int(inside.sum())


def ground_truth(box, labels):
    """Distance of the labelled vehicle that overlaps the box most, if their IoU is at least 0.5."""
    best_iou, best_distance = 0.0, np.nan
    for label_box, distance in labels:
        width = min(box[2], label_box[2]) - max(box[0], label_box[0])
        height = min(box[3], label_box[3]) - max(box[1], label_box[1])
        overlap = max(width, 0) * max(height, 0)
        union = (box[2] - box[0]) * (box[3] - box[1]) + (label_box[2] - label_box[0]) * (label_box[3] - label_box[1]) - overlap
        if overlap / union > best_iou:
            best_iou, best_distance = overlap / union, distance
    return best_distance if best_iou >= 0.5 else np.nan


# --- Pictures ---------------------------------------------------------------------------------------


def colour(depth):
    """Depth in metres to colours: near red, 80 m and beyond blue."""
    scaled = np.uint8(255 * (1 - np.clip(np.nan_to_num(depth, nan=80.0) / 80.0, 0, 1)))
    return cv2.applyColorMap(scaled, cv2.COLORMAP_JET)[..., ::-1]  # BGR colour map to RGB.


def draw(image, boxes, points=None, P=None):
    canvas = image.copy()
    if points is not None:  # Every lidar point in view, coloured by depth.
        ahead = points[points[:, 2] > 1.0]
        uvw = ahead @ P[:, :3].T + P[:, 3]
        u, v = (uvw[:, 0] / uvw[:, 2]).astype(int), (uvw[:, 1] / uvw[:, 2]).astype(int)
        seen = (u >= 0) & (u < canvas.shape[1] - 1) & (v >= 0) & (v < canvas.shape[0] - 1)
        for du, dv in ((0, 0), (1, 0), (0, 1), (1, 1)):  # 2x2 pixels per point, visible on large images.
            canvas[v[seen] + dv, u[seen] + du] = colour(ahead[seen, 2]).reshape(-1, 3)
    for number, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = box.astype(int)
        cx1, cy1, cx2, cy2 = (int(value) for value in centre(box))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 255, 255), 2)
        cv2.rectangle(canvas, (cx1, cy1), (cx2, cy2), (255, 255, 0), 1)  # The part used by M2 and M3.
        cv2.putText(canvas, str(number), (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return canvas


# --- Run -------------------------------------------------------------------------------------------


def main():
    yolo = YOLO("checkpoints/yolo26m.pt")  # COCO weights, downloaded on first use.
    depth_net = pipeline("depth-estimation", model=DEPTH_MODEL, device=DEVICE)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    frames = (("kitti", load_kitti), ("stf", load_stf), ("stf_snow", load_stf), ("shift", load_shift), ("shift_fog", load_shift))
    for name, load in frames:
        frame = load(DATA / name)
        image, P = frame["image"], frame["P"]
        result = yolo.predict(image[..., ::-1].copy(), classes=[2, 5, 7], imgsz=1280, conf=0.25, device=DEVICE, verbose=False)[0]
        boxes = result.boxes.xyxy.cpu().numpy()
        classes = [result.names[int(c)] for c in result.boxes.cls]
        depth = depth_net(Image.fromarray(image))["predicted_depth"].squeeze().cpu().numpy()

        print(f"\n{name.upper()}  {frame.get('note', '')}")
        print(f"f={P[1, 1]:.0f} px, horizon row={P[1, 2]:.0f}, camera height={frame['camera_height']:.2f} m")
        print(" #  class   M1 road  M1 height  M2 network  M3 lidar (points)      GT")
        for number, (box, cls) in enumerate(zip(boxes, classes), start=1):
            lidar, count = m3_lidar(box, frame["points"], P) if frame["points"] is not None else (np.nan, 0)
            row = dict(dataset=name, number=number, cls=cls, m1_road=m1_road(box, P, frame["camera_height"]),
                       m1_height=m1_height(box, P, cls), m2_network=m2_network(box, depth), m3_lidar=lidar,
                       lidar_points=count, gt=ground_truth(box, frame["labels"]))
            rows.append(row)
            print(f"{number:2d}  {cls:6s} {row['m1_road']:8.1f} {row['m1_height']:10.1f} {row['m2_network']:11.1f}"
                  f" {lidar:9.1f} ({count:4d}) {row['gt']:7.1f}")

        panels = [draw(image, boxes, frame["points"], P), draw(colour(depth), boxes)]
        if "depth_gt" in frame:
            panels.append(draw(colour(frame["depth_gt"]), boxes))
        cv2.imwrite(str(OUT / f"{name}.png"), cv2.cvtColor(np.vstack(panels), cv2.COLOR_RGB2BGR))

    with open(OUT / "distances.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nPictures and distances.csv saved to {OUT}")


if __name__ == "__main__":
    main()
