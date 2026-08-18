# ============================================================
#  hand_tracker.py
#  ──────────────────────────────────────────────────────────
#  This file handles ONE job: connect to MediaPipe and find
#  your hand in every webcam frame.
#
#  MediaPipe gives us 21 "landmarks" (key points) on the hand:
#
#       8   12  16  20      ← fingertips
#       7   11  15  19
#       6   10  14  18
#   4   5    9  13  17
#   3   2
#   1   0  ← wrist
#
#  We use these numbered points to figure out which fingers
#  are raised (in gesture.py).
# ============================================================

import cv2
import mediapipe as mp


class HandTracker:
    """
    Wraps MediaPipe Hands so the rest of our code stays simple.

    Usage:
        tracker = HandTracker()
        frame, landmarks_list = tracker.find_hands(frame)
    """

    def __init__(self, max_hands=2, detection_conf=0.7, tracking_conf=0.7):
        """
        Set up MediaPipe Hands.

        max_hands        : how many hands to track at once (1 or 2)
        detection_conf   : how confident MP must be before declaring a hand found
        tracking_conf    : how confident MP must be to keep tracking the hand
        """
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils

        # Create the MediaPipe Hands model
        self.hands = self.mp_hands.Hands(
            max_num_hands            = max_hands,
            min_detection_confidence = detection_conf,
            min_tracking_confidence  = tracking_conf
        )

    # ─────────────────────────────────────────────────────────
    def find_hands(self, frame, draw=True):
        """
        Process one webcam frame and return:
          - frame          : same frame, optionally with landmarks drawn on it
          - landmarks_list : a list of landmark objects (one per detected hand)

        Parameters:
            frame  : BGR image from OpenCV (numpy array)
            draw   : if True, draw the 21 dots + connections on the frame
        """
        # MediaPipe needs RGB, but OpenCV gives us BGR → convert
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run MediaPipe on this frame
        self.results = self.hands.process(rgb)

        landmarks_list = []  # will hold landmark data for each detected hand

        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:

                # Draw the skeleton on the frame if requested
                if draw:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        # Green dots for landmarks
                        self.mp_draw.DrawingSpec(color=(0, 255, 0),
                                                 thickness=2, circle_radius=4),
                        # White lines for connections
                        self.mp_draw.DrawingSpec(color=(255, 255, 255),
                                                 thickness=2)
                    )

                # Store this hand's landmarks (21 points)
                landmarks_list.append(hand_landmarks.landmark)

        return frame, landmarks_list

    # ─────────────────────────────────────────────────────────
    def get_palm_center(self, landmarks, frame_w, frame_h):
        """
        Returns the palm center as (x, y) pixel coordinates.

        We use landmark 9 (middle finger base joint) as the palm center.
        Landmarks are normalized (0.0–1.0), so we multiply by frame size
        to get real pixel positions.
        """
        x = int(landmarks[9].x * frame_w)
        y = int(landmarks[9].y * frame_h)
        return x, y
