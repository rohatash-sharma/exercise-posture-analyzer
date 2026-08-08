# AI/ML-Based Exercise Posture Analyzer

A working implementation of the pipeline described in the project proposal:
video input → MediaPipe pose estimation → 33-landmark extraction → joint
angle calculation → scope-of-error form validation → exercise state
machine → repetition counter → live dashboard.

## Files

| File | Architecture block(s) | Purpose |
|---|---|---|
| `pose_utils.py` | 2, 3, 4 | Wraps MediaPipe Pose; implements the `atan2`-based angle formula from Section 3.1 |
| `exercise_rules.py` | 5 | Joint triads and "scope of error" thresholds for squat / push-up / deadlift (Section 3.2) |
| `state_machine.py` | 6, 7 | Up/down (and lockout) state tracking; increments and tags reps as good/bad |
| `app.py` | 1, 8 | Streamlit UI: webcam capture, skeleton overlay, live rep counter, form feedback, audio cue |
| `requirements.txt` | — | Python dependencies |

## Setup

```bash
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

This opens a browser dashboard. Check **Start Camera** in the sidebar,
pick an exercise (Squat / Push-Up / Deadlift), and step back so your full
body is in frame.

## How it works

1. **Video Input Stream** — `cv2.VideoCapture(0)` grabs webcam frames.
2. **Pose Estimation** — each frame is passed to MediaPipe Pose, returning
   33 3D landmarks.
3. **Angle Calculation** — `calculate_angle()` computes the angle at a
   joint's vertex from three landmark points using
   `θ = |atan2(yC-yB, xC-xB) - atan2(yA-yB, xA-xB)|`.
4. **Form Validation** — `validate_form()` checks the relevant angles
   against each exercise's scope-of-error rules (e.g. squat knee angle
   < 90° ± 10°, back > 150°).
5. **Exercise State Machine** — `ExerciseStateMachine` tracks up/down
   transitions per exercise.
6. **Repetition Counter** — a rep is logged on each full state cycle and
   tagged "good" or "bad" depending on whether form held throughout.
7. **Dashboard** — Streamlit renders the annotated skeleton, rep count,
   current state, and live feedback; a terminal bell fires as a stand-in
   audio cue on each completed rep (swap `maybe_beep()` in `app.py` for a
   proper sound library like `playsound` or `pyttsx3` if you want spoken
   feedback).

## Extending

- **Add an exercise**: add an entry to `EXERCISE_CONFIG` in
  `exercise_rules.py` with its joint triads and thresholds, add matching
  logic in `validate_form()`, and extend `ExerciseStateMachine.update()`
  if it needs a different state pattern than up/down.
- **Swap the pose model**: `pose_utils.PoseEstimator` isolates MediaPipe;
  a YOLOv8-pose backend (mentioned in the proposal as an alternative) can
  be dropped in behind the same `process()` interface.
- **Video file input**: replace `cv2.VideoCapture(0)` in `app.py` with a
  file path, or add a Streamlit file-uploader for offline video analysis.

## Notes

- Requires a physical webcam on the machine running Streamlit — this
  won't work in a headless/server sandbox.
- MediaPipe currently supports Python 3.8–3.11; if `pip install` fails on
  a newer Python, use a 3.11 virtual environment.
