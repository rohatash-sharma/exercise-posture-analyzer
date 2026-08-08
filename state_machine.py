"""
state_machine.py
Blocks 6 & 7 of the System Flow Architecture:
  6. Exercise State Machine
  7. Repetition Counter

A rep only increments on a full state cycle (e.g. up -> down -> up for a
squat/push-up, or down -> lockout for a deadlift). Each rep is also tagged
"good" or "bad" depending on whether form validation failed at any point
during that rep -- this is the "rigorous repetition counter that only
increments when an exercise is performed within an acceptable scope of
error" described in Section 1 of the proposal. Reps still count when form
breaks (so the user sees their true total) but are logged separately as
bad reps, with feedback on why.
"""

from exercise_rules import EXERCISE_CONFIG


class ExerciseStateMachine:
    def __init__(self, exercise):
        if exercise not in EXERCISE_CONFIG:
            raise ValueError(f"Unknown exercise: {exercise}")
        self.exercise = exercise
        self.state = "up"  # up / down / lockout (deadlift only)
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
        the result of this frame's form validation.

        Returns the (possibly updated) state string.
        """
        config = EXERCISE_CONFIG[self.exercise]
        self.last_feedback = feedback

        if not form_ok:
            self.current_rep_clean = False

        if self.exercise in ("squat", "pushup"):
            down_thresh = config["down_threshold"] + config.get("tolerance", 0)
            up_thresh = config["up_threshold"]

            if self.state == "up" and primary_angle <= down_thresh:
                self.state = "down"
            elif self.state == "down" and primary_angle >= up_thresh:
                self.state = "up"
                self._complete_rep()

        elif self.exercise == "deadlift":
            start_thresh = config["start_threshold"]
            lockout_thresh = config["lockout_threshold"]

            if self.state == "up" and primary_angle <= start_thresh:
                self.state = "down"
            elif self.state == "down" and primary_angle >= lockout_thresh:
                self.state = "lockout"
                self._complete_rep()
            elif self.state == "lockout" and primary_angle <= start_thresh:
                self.state = "down"

        return self.state

    def reset(self):
        self.state = "up"
        self.rep_count = 0
        self.good_reps = 0
        self.bad_reps = 0
        self.current_rep_clean = True
        self.last_feedback = ""
