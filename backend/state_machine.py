"""
state_machine.py
Blocks 6 & 7 of the System Flow Architecture:
  6. Exercise State Machine
  7. Repetition Counter

Generic across all 16 exercises in exercise_rules.EXERCISE_CONFIG via the
"pattern" field:

  "flexion"   -> rest state is "up" (large angle). Angle drops below
                 low_threshold+tolerance to enter "down"; rising back above
                 high_threshold completes the rep and returns to "up".
                 (squat, push-up, lunge, bicep curl, sit-up, high knees,
                  mountain climber, tricep dip, pull-up, bicycle crunch)

  "extension" -> rest state is "down" (small angle). Angle rises above
                 high_threshold to enter "up"/"lockout"; dropping back below
                 low_threshold completes the rep and returns to "down".
                 (deadlift, shoulder press, jumping jack, lateral raise,
                  glute bridge, calf raise)

A rep only counts as "good" if form validation passed on every frame of
that rep -- the "rigorous repetition counter" described in the proposal.
Reps still increment on bad form (so the total is accurate) but are
tagged separately with the feedback that caused the flag.
"""

from exercise_rules import EXERCISE_CONFIG


class ExerciseStateMachine:
    def __init__(self, exercise):
        if exercise not in EXERCISE_CONFIG:
            raise ValueError(f"Unknown exercise: {exercise}")
        self.exercise = exercise
        self.pattern = EXERCISE_CONFIG[exercise]["pattern"]
        # "flexion" rests at "up"; "extension" rests at "down"
        self.state = "up" if self.pattern == "flexion" else "down"
        self.rep_count = 0
        self.good_reps = 0
        self.bad_reps = 0
        self.current_rep_clean = True
        self.last_feedback = ""

    def _complete_rep(self):
        self.rep_count += 1
        if self.current_rep_clean:
            self.good_reps += 1
        else:
            self.bad_reps += 1
        self.current_rep_clean = True

    def update(self, primary_angle, form_ok, feedback):
        """
        Advance the state machine given the current primary joint angle and
        this frame's form-validation result. Returns the (possibly updated)
        state string.
        """
        if primary_angle is None:
            return self.state

        config = EXERCISE_CONFIG[self.exercise]
        self.last_feedback = feedback

        if not form_ok:
            self.current_rep_clean = False

        low = config["low_threshold"] + config.get("tolerance", 0)
        high = config["high_threshold"]

        if self.pattern == "flexion":
            if self.state == "up" and primary_angle <= low:
                self.state = "down"
            elif self.state == "down" and primary_angle >= high:
                self.state = "up"
                self._complete_rep()

        elif self.pattern == "extension":
            if self.state == "down" and primary_angle >= high:
                self.state = "up"
                self._complete_rep()
            elif self.state == "up" and primary_angle <= low:
                self.state = "down"

        return self.state

    def reset(self):
        self.state = "up" if self.pattern == "flexion" else "down"
        self.rep_count = 0
        self.good_reps = 0
        self.bad_reps = 0
        self.current_rep_clean = True
        self.last_feedback = ""
