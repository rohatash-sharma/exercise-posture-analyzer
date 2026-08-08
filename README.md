# AI/ML-Based Exercise Posture Analyzer

Real-time pose estimation, biomechanical form validation, and a rigorous
repetition counter, covering 16 exercises. The pipeline: video input →
MediaPipe pose estimation → 33-landmark extraction → joint angle
calculation → scope-of-error form validation → exercise state machine →
repetition counter → dashboard.

```
exercise/
├── backend/
│   ├── app.py               # Streamlit dashboard (video input + UI)
│   ├── exercise_rules.py    # 16-exercise config + form validation
│   ├── pose_utils.py        # MediaPipe wrapper + angle formula
│   ├── state_machine.py     # Generic rep state machine
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Static overview page
│   ├── style.css
│   └── main.js
├── .gitignore
└── README.md
```

## Backend (does the actual analysis)

```bash
cd backend
pip install -r requirements.txt
streamlit run app.py
```

Requires a webcam on the machine you run this on. Opens a browser
dashboard where you pick an exercise, start the camera, and see live
rep counts, form feedback, and a skeleton overlay.

See [`backend/`](./backend) — each file maps to one stage of the
pipeline; details are in the module docstrings.

## Frontend (static overview page)

```bash
cd frontend
python -m http.server 8000   # or just open index.html directly
```

This is a **static, standalone page** — it visualizes the product's
core idea (joint-angle math) and lists the 16 exercises, but it does
not call the Python backend or your webcam. The two folders don't share
code; if you want the frontend to actually trigger analysis, it would
need to call the backend over an API, which isn't built here.

`frontend/main.js` keeps a JS mirror of the exercise list for display
purposes — if you add or edit an exercise in
`backend/exercise_rules.py`, update the `EXERCISES` array in
`frontend/main.js` to match.

## Exercises included

Squat, Push-Up, Deadlift, Lunge, Bicep Curl, Shoulder Press,
Sit-Up/Crunch, Jumping Jack, High Knees, Lateral Raise, Tricep Dip,
Glute Bridge, Mountain Climber, Calf Raise, Pull-Up, Bicycle Crunch.

## Adding an exercise

Add one entry to `EXERCISE_CONFIG` in `backend/exercise_rules.py`:
joint `triads`, a `primary_angle`, a `pattern` (`"flexion"` if the
angle drops during the active phase like a squat, `"extension"` if it
rises like a deadlift), thresholds, and optional `form_rules`. No
changes needed in `state_machine.py` or `app.py`. Mirror the new entry
in `frontend/main.js`'s `EXERCISES` array if you want it listed on the
overview page.
