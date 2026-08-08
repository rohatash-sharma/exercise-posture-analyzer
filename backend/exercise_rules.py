"""
exercise_rules.py
Block 5 of the System Flow Architecture: Form Validation (Scope of Error Logic)

This is a config-driven system: adding a new exercise means adding one
entry to EXERCISE_CONFIG, not writing new branching code. Each exercise
declares:

  - triads: named joint angles to compute (landmark triples)
  - primary_angle: which named angle(s) drive the rep state machine
                    (averaged left/right if both given)
  - pattern:
      "flexion"   -> angle DROPS during the active phase, then rises back
                     up to complete the rep (squat, push-up, bicep curl...)
      "extension" -> angle RISES during the active phase, then drops back
                     down to complete the rep (jumping jack, glute bridge...)
  - low_threshold / high_threshold / tolerance: the "scope of error" bounds
    from Section 3.2 of the proposal
  - form_rules: extra checks applied while in a given state, e.g. "back
    must stay above 150 degrees while in the down position"

state_machine.py consumes this config generically -- see that file for how
`pattern` drives the up/down/lockout transitions.
"""

import mediapipe as mp
from pose_utils import calculate_angle, get_landmark_xy

mp_pose = mp.solutions.pose
LM = mp_pose.PoseLandmark

# Shorthand landmark triads reused across several exercises
KNEE = lambda side: (getattr(LM, f"{side}_HIP"), getattr(LM, f"{side}_KNEE"), getattr(LM, f"{side}_ANKLE"))
HIP = lambda side: (getattr(LM, f"{side}_SHOULDER"), getattr(LM, f"{side}_HIP"), getattr(LM, f"{side}_KNEE"))
ELBOW = lambda side: (getattr(LM, f"{side}_SHOULDER"), getattr(LM, f"{side}_ELBOW"), getattr(LM, f"{side}_WRIST"))
SHOULDER_ABD = lambda side: (getattr(LM, f"{side}_HIP"), getattr(LM, f"{side}_SHOULDER"), getattr(LM, f"{side}_ELBOW"))
BODY_LINE = lambda side: (getattr(LM, f"{side}_SHOULDER"), getattr(LM, f"{side}_HIP"), getattr(LM, f"{side}_ANKLE"))
ANKLE = lambda side: (getattr(LM, f"{side}_KNEE"), getattr(LM, f"{side}_ANKLE"), getattr(LM, f"{side}_FOOT_INDEX"))


def _bilateral(fn):
    """Build {'left': fn('LEFT'), 'right': fn('RIGHT')} triads."""
    return {"left": fn("LEFT"), "right": fn("RIGHT")}


EXERCISE_CONFIG = {

    "squat": {
        "display_name": "Squat",
        "triads": {**_bilateral(KNEE), "back_left": HIP("LEFT"), "back_right": HIP("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 10, "high_threshold": 160,
        "form_rules": [
            {"angle": ["back_left", "back_right"], "state": "down", "min": 150,
             "message": "Keep your back straighter"},
        ],
    },

    "pushup": {
        "display_name": "Push-Up",
        "triads": {**_bilateral(ELBOW), "line_left": BODY_LINE("LEFT"), "line_right": BODY_LINE("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 0, "high_threshold": 160,
        "form_rules": [
            {"angle": ["line_left", "line_right"], "state": "down", "min": 165, "max": 195,
             "message": "Keep your body in a straight line (avoid hip sag/pike)"},
        ],
    },

    "deadlift": {
        "display_name": "Deadlift",
        "triads": _bilateral(HIP),
        "primary_angle": ["left", "right"],
        "pattern": "extension", "low_threshold": 100, "high_threshold": 170,
        "form_rules": [
            {"angle": ["left", "right"], "state": "down", "min": 150,
             "message": "Warning: back rounding detected"},
        ],
    },

    "lunge": {
        "display_name": "Lunge",
        "triads": {**_bilateral(KNEE), "back_left": HIP("LEFT"), "back_right": HIP("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 15, "high_threshold": 160,
        "form_rules": [
            {"angle": ["back_left", "back_right"], "state": "down", "min": 150,
             "message": "Keep your torso upright"},
        ],
    },

    "bicep_curl": {
        "display_name": "Bicep Curl",
        "triads": {**_bilateral(ELBOW), "sway_left": SHOULDER_ABD("LEFT"), "sway_right": SHOULDER_ABD("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 45, "tolerance": 10, "high_threshold": 150,
        "form_rules": [
            {"angle": ["sway_left", "sway_right"], "state": "any", "max": 40,
             "message": "Avoid swinging your shoulders/elbows"},
        ],
    },

    "shoulder_press": {
        "display_name": "Shoulder Press",
        "triads": {**_bilateral(ELBOW), "arm_left": SHOULDER_ABD("LEFT"), "arm_right": SHOULDER_ABD("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "extension", "low_threshold": 90, "high_threshold": 160,
        "form_rules": [
            {"angle": ["arm_left", "arm_right"], "state": "up", "min": 150,
             "message": "Press arms fully overhead"},
        ],
    },

    "situp": {
        "display_name": "Sit-Up / Crunch",
        "triads": _bilateral(HIP),
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 15, "high_threshold": 140,
        "form_rules": [],
    },

    "jumping_jack": {
        "display_name": "Jumping Jack",
        "triads": _bilateral(SHOULDER_ABD),
        "primary_angle": ["left", "right"],
        "pattern": "extension", "low_threshold": 30, "high_threshold": 150,
        "form_rules": [],
    },

    "high_knees": {
        "display_name": "High Knees",
        "triads": _bilateral(HIP),
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 100, "tolerance": 15, "high_threshold": 160,
        "form_rules": [],
    },

    "lateral_raise": {
        "display_name": "Lateral Raise",
        "triads": {**_bilateral(SHOULDER_ABD), "elbow_left": ELBOW("LEFT"), "elbow_right": ELBOW("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "extension", "low_threshold": 20, "high_threshold": 85,
        "form_rules": [
            {"angle": ["elbow_left", "elbow_right"], "state": "up", "min": 150,
             "message": "Keep your arms straight"},
        ],
    },

    "tricep_dip": {
        "display_name": "Tricep Dip",
        "triads": _bilateral(ELBOW),
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 10, "high_threshold": 160,
        "form_rules": [],
    },

    "glute_bridge": {
        "display_name": "Glute Bridge",
        "triads": _bilateral(HIP),
        "primary_angle": ["left", "right"],
        "pattern": "extension", "low_threshold": 110, "high_threshold": 170,
        "form_rules": [],
    },

    "mountain_climber": {
        "display_name": "Mountain Climber",
        "triads": {**_bilateral(HIP), "line_left": BODY_LINE("LEFT"), "line_right": BODY_LINE("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 15, "high_threshold": 160,
        "form_rules": [
            {"angle": ["line_left", "line_right"], "state": "any", "min": 160,
             "message": "Keep hips level, avoid piking"},
        ],
    },

    "calf_raise": {
        "display_name": "Calf Raise",
        "triads": {**_bilateral(ANKLE), "knee_left": KNEE("LEFT"), "knee_right": KNEE("RIGHT")},
        "primary_angle": ["left", "right"],
        "pattern": "extension", "low_threshold": 70, "high_threshold": 110,
        "form_rules": [
            {"angle": ["knee_left", "knee_right"], "state": "any", "min": 165,
             "message": "Keep your knees straight"},
        ],
    },

    "pullup": {
        "display_name": "Pull-Up",
        "triads": _bilateral(ELBOW),
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 70, "tolerance": 15, "high_threshold": 160,
        "form_rules": [],
    },

    "bicycle_crunch": {
        "display_name": "Bicycle Crunch",
        "triads": _bilateral(HIP),
        "primary_angle": ["left", "right"],
        "pattern": "flexion", "low_threshold": 90, "tolerance": 15, "high_threshold": 150,
        "form_rules": [],
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


def _avg(angles, keys):
    vals = [angles[k] for k in keys if k in angles]
    return sum(vals) / len(vals) if vals else None


def validate_form(exercise, angles, state):
    """
    Applies the exercise's scope-of-error form_rules generically.

    Returns:
        (form_ok: bool, feedback: str, primary_angle: float)
    """
    config = EXERCISE_CONFIG[exercise]
    primary_angle = _avg(angles, config["primary_angle"])

    feedback = []
    form_ok = True

    for rule in config["form_rules"]:
        if rule["state"] != "any" and rule["state"] != state:
            continue
        val = _avg(angles, rule["angle"])
        if val is None:
            continue
        if "min" in rule and val < rule["min"]:
            form_ok = False
            feedback.append(rule["message"])
        if "max" in rule and val > rule["max"]:
            form_ok = False
            feedback.append(rule["message"])

    return form_ok, "; ".join(feedback) if feedback else "Good form", primary_angle
