# 🌸 Bloom — Hand Gesture Flower Animation

## About This Project

**Project 02: Bloom — Real-Time Hand Gesture Flower Animation System**

The Bloom Hand Gesture Flower Animation System is a technology-based project designed to create interactive visual art using real-time hand tracking through a standard webcam. The system detects hand positions and finger gestures using artificial intelligence and responds by generating animated flowers on screen that grow, bloom, and move in sync with the user's hand movements.

By combining computer vision, gesture recognition, and real-time graphics animation, the system aims to demonstrate how technology can bridge human movement and digital art — allowing users to control a living, blooming visual experience simply by moving their hands in front of a camera, with no additional hardware or controllers required.

---

**Bloom** is a real-time hand gesture project that uses your webcam to detect your hand movements and displays beautiful animated flowers on screen that react to your gestures. It is built entirely in Python using MediaPipe (hand tracking), OpenCV (camera), and Pygame (graphics).

There are **two modes**:

| Mode | File | Gesture |
|------|------|---------|
| 🌌 **Meteor Orbit** | `main.py` | Open / close fingers to control a galaxy of flowers orbiting your palm |
| 🌸 **Bouquet Pinch** | `main2.py` | Pinch fingers together (Italian 🤌 gesture) to hide flowers; open fingers to make a bouquet bloom with stems |

---

## 📸 What It Does

- Tracks your hand in real time using your webcam  
- Displays animated flowers that follow your hand position  
- Flowers grow, bloom, sparkle, and close based on your finger gestures  
- Works with **one or two hands** simultaneously  
- No internet connection needed — runs fully offline

---

## 🖥️ System Requirements

- **OS:** Windows 10 or Windows 11  
- **Python:** 3.11 (important — not 3.12 or 3.13)  
- **Webcam:** Any USB or built-in webcam  
- **RAM:** 4 GB minimum  

> ⚠️ Close **Microsoft Teams** and **Zoom** before running. They lock the webcam and cause a black screen.

---

## ⚙️ Setup — Step by Step

### 1. Install Python 3.11

Download from: https://www.python.org/downloads/release/python-3119/

During installation, **check the box** that says "Add Python to PATH".

After installing, open PowerShell and confirm:
```powershell
py -3.11 --version
```
It should print `Python 3.11.x`.

---

### 2. Download the Project

**Option A — With Git:**
```powershell
git clone https://github.com/vithuckshana/Bloom_v.git
cd Bloom_v
```

**Option B — Without Git:**  
Go to https://github.com/vithuckshana/Bloom_v → click **Code → Download ZIP** → extract the folder.

---

### 3. Create a Virtual Environment

Inside the project folder, run:
```powershell
py -3.11 -m venv venv
```

This creates an isolated Python environment so the project libraries don't interfere with anything else on your PC.

---

### 4. Install Required Libraries

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

This installs:
- `mediapipe` — hand tracking AI
- `opencv-python` — webcam access
- `pygame` — graphics and animation
- `numpy` — math support

Installation may take 2–5 minutes depending on your internet speed.

---

## ▶️ How to Run

### Mode 1 — Meteor Orbit (main.py)
```powershell
.\venv\Scripts\python.exe main.py
```

### Mode 2 — Bouquet Pinch (main2.py)
```powershell
.\venv\Scripts\python.exe main2.py
```

---

## 🖐️ How to Use

### Mode 1 — `main.py` (Meteor Orbit)

| Your Gesture | What Happens |
|---|---|
| Open all fingers wide | 7 flowers orbit fast in a wide ring with glowing comet tails |
| Close into a fist | Flowers shrink and orbit slowly in a tight cluster |
| Move your hand | The whole orbit follows your palm |
| Use both hands | Two separate orbits appear! |
| Press `ESC` | Quit the program |

---

### Mode 2 — `main2.py` (Bouquet Pinch)

| Your Gesture | What Happens |
|---|---|
| Pinch all fingers together 🤌 | Flowers are completely hidden |
| Slowly open your fingers | Stems grow upward → buds appear → petals unfold → sparkles burst! |
| Pinch closed again | Flowers fold away and disappear |
| Move your hand | The whole bouquet follows your palm smoothly |
| Use both hands | Two separate bouquets! |
| Press `ESC` | Quit the program |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Black screen / no camera | Close Teams and Zoom, then restart the app |
| `mediapipe` not found | Re-run `pip install -r requirements.txt` inside the venv |
| Flowers lag / slow | Make sure no heavy apps are running in the background |
| Hand not detected | Ensure good lighting — face your palm toward the camera |
| Python version error | Use exactly Python 3.11 — not 3.12 or 3.13 |

---

## 📁 Project Structure

```
Bloom_v/
│
├── main.py           # Mode 1: Meteor orbit flower animation
├── main2.py          # Mode 2: Bouquet with stems (pinch gesture)
├── hand_tracker.py   # Webcam + MediaPipe hand landmark detector
├── gesture.py        # Converts hand landmarks into bloom levels
├── flower.py         # Meteor flower animation classes
├── requirements.txt  # Python library versions
└── README.md         # This file
```

---

## 📚 Libraries Used

| Library | Version | Purpose |
|---|---|---|
| `mediapipe` | 0.10.14 | AI hand tracking (21 landmarks) |
| `opencv-python` | 4.10.0.84 | Webcam capture |
| `pygame` | 2.6.1 | Window, drawing, animation |
| `numpy` | 2.4.6 | Array math |

---

## 👤 Author

**Vithuckshana**  
GitHub: https://github.com/vithuckshana/Bloom_v
