"""
exercise_rules.py
Block 5 of the System Flow Architecture: Form Validation (Scope of Error Logic)

Encodes the exercise-specific rules from Section 3.2 of the proposal:

  Squat:    "down" state = knee angle < 90 deg (+/- 10 deg tolerance);
            back must stay relatively straight (shoulder-hip-knee alignment).
  Push-Up:  "down" state = elbow angle <= 90 deg;
            body alignment (shoulder-hip-ankle) must stay near 180 deg (+/- 15 deg).
  Deadlift: back-angle monitored throughout to prevent rounding;
            tracked from initial pull (knee extension) to lockout (hip
            extension approaching 180 deg).
"""

import mediapipe as mp
from pose_utils import calculate_angle, get_landmark_xy

mp_pose = mp.solutions.pose
LM = mp_pose.PoseLandmark

EXERCISE_CONFIG = {
    "squat": {
        "primary_joint": "knee",
        "triads": {
            "left_knee":  (LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE),
            "right_knee": (LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE),
            "left_back":  (LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.LEFT_KNEE),
            "right_back": (LM.RIGHT_SHOULDER, LM.RIGHT_HIP, LM.RIGHT_KNEE),
        },
        "down_threshold": 90,   # knee angle must drop below this
        "tolerance": 10,        # +/- 10 deg scope of error
        "up_threshold": 160,    # near-standing = "up" transition
        "back_min_angle": 150,  # back must stay relatively straight in "down"
    },
    "pushup": {
        "primary_joint": "elbow",
        "triads": {
            "left_elbow":  (LM.LEFT_SHOULDER, LM.LEFT_ELBOW, LM.LEFT_WRIST),
            "right_elbow": (LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW, LM.RIGHT_WRIST),
            "left_body":   (LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.LEFT_ANKLE),
            "right_body":  (LM.RIGHT_SHOULDER, LM.RIGHT_HIP, LM.RIGHT_ANKLE),
        },
        "down_threshold": 90,   # elbow angle must reach <= this
        "tolerance": 0,
        "up_threshold": 160,
        "body_line_target": 180,
        "body_line_tolerance": 15,
    },
    "deadlift": {
        "primary_joint": "hip",
        "triads": {
            "left_hip":   (LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.LEFT_KNEE),
            "right_hip":  (LM.RIGHT_SHOULDER, LM.RIGHT_HIP, LM.RIGHT_KNEE),
            "left_knee":  (LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE),
            "right_knee": (LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE),
        },
        "start_threshold": 100,   # bent-over pull-initiation position
        "lockout_threshold": 170, # hip extension approaching 180 deg at lockout
        "back_min_angle": 150,    # shoulder-hip-knee proxy for back rounding
    },
}


def extract_angles(landmarks, exercise, width, height):
    """
    Computes every joint angle defined for `exercise` in EXERCISE_CONFIG.

    Returns:
        (angles: dict[str, float], avg_visibility: float)
    """
    config = EXERCISE_CONFIG[exercise]
    angles = {}
    visibilities = []

    for name, (p1, p2, p3) in config["triads"].items():
        a = get_landmark_xy(landmarks, p1.value, width, height)
        b = get_landmark_xy(landmarks, p2.value, width, height)
        c = get_landmark_xy(landmarks, p3.value, width, height)
        visibilities.extend([a[2], b[2], c[2]])
        angles[name] = calculate_angle(a, b, c)

    avg_visibility = sum(visibilities) / len(visibilities) if visibilities else 0.0
    return angles, avg_visibility


def validate_form(exercise, angles, state):
    """
    Applies the exercise-specific "scope of error" rules.

    Returns:
        (form_ok: bool, feedback: str, primary_angle: float)
        primary_angle is the averaged left/right angle that the
        ExerciseStateMachine uses to drive state transitions.
    """
    config = EXERCISE_CONFIG[exercise]
    feedback = []
    form_ok = True

    if exercise == "squat":
        knee_avg = (angles["left_knee"] + angles["right_knee"]) / 2
        back_avg = (angles["left_back"] + angles["right_back"]) / 2

        if state == "down" and back_avg < config["back_min_angle"]:
            form_ok = False
            feedback.append("Keep your back straighter")

        return form_ok, "; ".join(feedback) if feedback else "Good form", knee_avg

    elif exercise == "pushup":
        elbow_avg = (angles["left_elbow"] + angles["right_elbow"]) / 2
        body_avg = (angles["left_body"] + angles["right_body"]) / 2

        target, tol = config["body_line_target"], config["body_line_tolerance"]
        if state == "down" and not (target - tol <= body_avg <= target + tol):
            form_ok = False
            feedback.append("Keep your body in a straight line (avoid hip sag/pike)")

        return form_ok, "; ".join(feedback) if feedback else "Good form", elbow_avg

    elif exercise == "deadlift":
        hip_avg = (angles["left_hip"] + angles["right_hip"]) / 2

        if hip_avg < config["back_min_angle"] and state == "down":
            form_ok = False
            feedback.append("Warning: back rounding detected")

        return form_ok, "; ".join(feedback) if feedback else "Good form", hip_avg

    return True, "", 0.0
