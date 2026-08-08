"""
app.py
Blocks 1 & 8 of the System Flow Architecture:
  1. Video Input Stream
  8. User UI Dashboard & Audio Feedback

Run with:
    streamlit run app.py

Requires a webcam attached to the machine this is run on.
"""

import time

import cv2
import mediapipe as mp
import streamlit as st

from pose_utils import PoseEstimator
from exercise_rules import EXERCISE_CONFIG, extract_angles, validate_form
from state_machine import ExerciseStateMachine

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

st.set_page_config(page_title="AI Posture Analyzer", layout="wide")
st.title("AI/ML-Based Exercise Posture Analyzer")
st.caption(
    "Real-time pose estimation, biomechanical form validation, and a "
    "rigorous repetition counter -- built on MediaPipe Pose (BlazePose)."
)

# ---------------------------------------------------------------- Sidebar --
st.sidebar.header("Controls")
exercise = st.sidebar.selectbox(
    "Select Exercise", list(EXERCISE_CONFIG.keys()), format_func=str.title
)
run = st.sidebar.checkbox("Start Camera")
reset_btn = st.sidebar.button("Reset Counter")
audio_on = st.sidebar.checkbox("Audio feedback (rep beep)", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Scope-of-error rules**\n\n"
    + {
        "squat": "- Knee angle < 90° (±10°) = down\n- Back must stay > 150° "
                 "(shoulder-hip-knee)",
        "pushup": "- Elbow angle ≤ 90° = down\n- Body line 180° (±15°)",
        "deadlift": "- Hip angle ≥ 170° = lockout\n- Back monitored for "
                    "rounding throughout the pull",
    }[exercise]
)

# --------------------------------------------------------- Session state --
if "state_machine" not in st.session_state or st.session_state.get("exercise") != exercise:
    st.session_state.state_machine = ExerciseStateMachine(exercise)
    st.session_state.exercise = exercise
    st.session_state.last_rep_count = 0

if reset_btn:
    st.session_state.state_machine.reset()
    st.session_state.last_rep_count = 0

sm = st.session_state.state_machine

# --------------------------------------------------------------- Layout ---
col1, col2 = st.columns([3, 1])
frame_placeholder = col1.empty()
rep_placeholder = col2.empty()
good_bad_placeholder = col2.empty()
state_placeholder = col2.empty()
feedback_placeholder = col2.empty()


def draw_dashboard(frame, sm, feedback, form_ok):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 95), (20, 20, 20), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

    cv2.putText(frame, f"Exercise: {sm.exercise.title()}", (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Reps: {sm.rep_count}  (Good {sm.good_reps} / Bad {sm.bad_reps})",
                (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    color = (0, 220, 0) if form_ok else (0, 0, 255)
    cv2.putText(frame, f"State: {sm.state.upper()}", (15, 82),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def maybe_beep():
    """Simple terminal bell as a lightweight stand-in for audio feedback."""
    try:
        print("\a", end="", flush=True)
    except Exception:
        pass


# ------------------------------------------------------------- Main loop --
if run:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Could not open the webcam. Check camera permissions/index.")
    else:
        estimator = PoseEstimator()

        while run and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.warning("Lost camera feed.")
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = estimator.process(rgb)

            form_ok, feedback = True, "No person detected"

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 200, 255), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2),
                )
                landmarks = results.pose_landmarks.landmark
                angles, visibility = extract_angles(landmarks, exercise, w, h)

                if visibility > 0.5:
                    form_ok, feedback, primary_angle = validate_form(exercise, angles, sm.state)
                    sm.update(primary_angle, form_ok, feedback)
                else:
                    feedback = "Move fully into frame"

            frame = draw_dashboard(frame, sm, feedback, form_ok)
            frame_placeholder.image(frame, channels="BGR", use_container_width=True)

            rep_placeholder.metric("Total Reps", sm.rep_count)
            good_bad_placeholder.write(f"✅ Good: {sm.good_reps}   ❌ Bad: {sm.bad_reps}")
            state_placeholder.write(f"**State:** {sm.state.upper()}")
            (feedback_placeholder.success if form_ok else feedback_placeholder.error)(feedback)

            if audio_on and sm.rep_count != st.session_state.last_rep_count:
                maybe_beep()
                st.session_state.last_rep_count = sm.rep_count

            time.sleep(0.01)

        cap.release()
        estimator.close()
else:
    st.info("Check **Start Camera** in the sidebar to begin analysis.")
