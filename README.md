# fogrange-monocular-vehicle-distance

How far away is the car ahead, seen by a single camera, in fog, snow or rain? We compare three ways to measure it.
All of them start from the same box around a car found by YOLO:

| | Method | Distance from |
|---|---|---|
| **M1** | Geometry | the bottom edge of the box on a flat road, or the box height and a typical car height |
| **M2** | Depth network | the median of the Depth Anything V2 Metric depth map in the centre of the box |
| **M3** | Lidar | the median depth of the lidar points falling into the centre of the box |

The ground truth is the distance to the nearest face of the labelled 3D box. The main part of the project will be
fine-tuning Depth Anything V2 Metric on simulated fog and rain (SHIFT) and testing it on real bad weather (Seeing Through Fog).

## Current state

One good-weather frame from each dataset and one bad-weather frame from Seeing Through Fog and SHIFT go through all
three methods (KITTI is good weather only):

| Dataset | Weather | Frame | Image | Lidar | 3D labels |
|---|---|---|---|---|---|
| KITTI | clear | 000007, from a public repository with a few KITTI frames | yes | yes | yes |
| Seeing Through Fog | clear | the authors' example frame (split `train_clear_day`) | yes | yes | no, they need registration |
| Seeing Through Fog | snow | another example frame, `2018-02-12_15-39-23_00100` (split `snow_day`) | yes | no, needs registration | no, needs registration |
| SHIFT | clear | sequence `0094-23d0`, frame 400 (noon), from an unofficial mirror | yes | no | yes, plus the simulator depth map |
| SHIFT | heavy fog | sequence `0804-e4f8`, frame 0 (daytime) | yes | no | yes, plus the simulator depth map |

## Run

```bash
uv venv --python 3.13 .venv
```

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

```bash
.venv/bin/python scripts/fetch_samples.py
```

```bash
.venv/bin/python scripts/three_methods.py
```

The second script prints a table per frame and saves `results/one_frame/{kitti,stf,stf_snow,shift,shift_fog}.png`
and `distances.csv`. The YOLO26m weights (44 MB) and Depth Anything V2 Metric Small (99 MB) download on first use.

## Course materials

The project description, schedule and first presentation (in Polish) are in [`materialy/`](materialy/).

## Licences

Code: AGPL-3.0 (see `LICENSE`), because Ultralytics YOLO is AGPL-3.0. Data is not included and must not be committed:
KITTI is CC BY-NC-SA 3.0, SHIFT CC BY-NC-SA 4.0, and the Seeing Through Fog terms of use forbid passing the data on and
require anonymised people and licence plates in published images.
