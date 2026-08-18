# ============================================================
#  gesture.py
#  ──────────────────────────────────────────────────────────
#  This file reads the 21 hand landmarks and answers ONE
#  question:  "How open is the hand right now?"
#
#  It returns a bloom_level between 0.0 and 1.0:
#      0.0  →  fist (all fingers down)
#      0.2  →  1 finger up
#      0.4  →  2 fingers up
#      0.6  →  3 fingers up
#      0.8  →  4 fingers up
#      1.0  →  open hand (all 5 fingers up)
# ============================================================


def count_fingers(landmarks):
    """
    Count how many fingers are raised.

    How it works:
    ─────────────
    For each finger we compare TWO landmark points:

        ● Fingertip  (top of finger)
        ● PIP joint  (middle knuckle)

    If the fingertip's Y coordinate is LESS than the PIP joint's Y,
    the finger is pointing UP (remember: Y=0 is the top of the screen).

    Thumb is special — we compare X coordinates instead of Y,
    because the thumb moves sideways.

    Finger  │ Tip landmark │ PIP landmark
    ────────┼──────────────┼─────────────
    Thumb   │     4        │     2
    Index   │     8        │     6
    Middle  │    12        │    10
    Ring    │    16        │    14
    Pinky   │    20        │    18
    """

    count = 0

    # ── Thumb ─────────────────────────────────────────────
    # Tip (4) to the LEFT of IP joint (3) = thumb extended
    # We use landmark[2] (MCP) as reference for more reliability
    if landmarks[4].x < landmarks[2].x:
        count += 1

    # ── Four Fingers ──────────────────────────────────────
    # Tip Y < PIP Y means finger is up (Y axis is flipped on screen)
    finger_tips = [8,  12, 16, 20]   # index, middle, ring, pinky tips
    finger_pips = [6,  10, 14, 18]   # their middle knuckles

    for tip_id, pip_id in zip(finger_tips, finger_pips):
        if landmarks[tip_id].y < landmarks[pip_id].y:
            count += 1

    return count   # 0 to 5


def get_bloom_level(landmarks):
    """
    Convert hand landmarks into a bloom_level from 0.0 → 1.0.

    This is the main number that controls how open the flower is.
    """
    fingers_up = count_fingers(landmarks)
    bloom_level = fingers_up / 5.0
    return bloom_level


def get_palm_position(landmarks, frame_w, frame_h):
    """
    Return the palm center as pixel (x, y).

    Landmark 9 is the base of the middle finger — a stable,
    central point that represents the palm well.
    """
    x = int(landmarks[9].x * frame_w)
    y = int(landmarks[9].y * frame_h)
    return x, y
