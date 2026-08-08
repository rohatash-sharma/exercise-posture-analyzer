"""
pose_utils.py
Blocks 2 & 3 & 4 of the System Flow Architecture:
  2. MediaPipe / YOLO (Pose Estimation)
  3. Extract 33 3D Landmarks
  4. Angle Calculation

Implements the biomechanical angle formula from Section 3.1 of the proposal:

    theta = |atan2(yC - yB, xC - xB) - atan2(yA - yB, xA - xB)|

where A, C are the outer points of a joint triad and B is the vertex.
"""

import numpy as np
import mediapipe as mp

mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    """
    Calculate the angle at vertex b formed by points a-b-c.

    a, b, c: iterables of at least (x, y) -- a 3rd element (e.g. visibility
              or z) is ignored for the 2D angle calculation.

    Returns:
        angle in degrees, clamped to the range [0, 180].
    """
    a = np.array(a[:2], dtype=float)
    b = np.array(b[:2], dtype=float)
    c = np.array(c[:2], dtype=float)

    radians = (np.arctan2(c[1] - b[1], c[0] - b[0]) -
               np.arctan2(a[1] - b[1], a[0] - b[0]))
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360.0 - angle

    return float(angle)


def get_landmark_xy(landmarks, idx, image_width, image_height):
    """
    Convert a normalized MediaPipe landmark to pixel coordinates.

    Returns:
        (x_px, y_px, visibility)
    """
    lm = landmarks[idx]
    return (lm.x * image_width, lm.y * image_height, lm.visibility)


class PoseEstimator:
    """
    Thin wrapper around MediaPipe Pose (BlazePose) -- the 33-landmark,
    3D pose estimation model referenced in Section 2 of the proposal.
    """

    def __init__(self, min_detection_confidence=0.6, min_tracking_confidence=0.6,
                 model_complexity=1):
        self.pose = mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity,
        )

    def process(self, frame_rgb):
        """frame_rgb: an RGB numpy image. Returns MediaPipe's results object."""
        return self.pose.process(frame_rgb)

    def close(self):
        self.pose.close()
