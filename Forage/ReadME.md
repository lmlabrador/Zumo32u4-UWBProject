# Foraging Controller for Zumo Robot

This project implements a foraging behavior controller for a Zumo robot using computer vision and Ultra-Wideband (UWB) localization. The robot uses a Raspberry Pi camera and UWB positioning to locate, approach, and transport colored pucks toward a predefined goal location.

## Overview

The system utilizes:

- **Raspberry Pi Camera** for visual puck detection.
- **UWBReader** for positioning.
- **Zumo Robot** for motion control.
- A **region of interest (ROI)** defined horizontally in the camera's view to focus the detection area.

## How It Works

1. **Initialization**: Configures hardware, video stream, and ROI mask.
2. **Vision-Based Detection**: Detects pucks using HSV color filtering within a ROI.
3. **UWB Positioning**: Tracks robot's current location using an attached UWB module.
4. **Control Logic**:
   - Turns in place if no puck is found.
   - When a puck is detected, adjusts its heading based on the puck's position and attraction toward the goal.
5. **Debug Interface**: Optionally shows a debug video window with overlays for puck detection, UWB location, and motor states.

## Parameters

### Configuration

```python
RESOLUTION = (320, 240)
GOAL_POSITION = (3.4, 1.5)
UWB_PORT = "/dev/ttyUWB"
SHOW_VIDEO = True
DEBUG_PRINTS = True
```

### Motion Control

```python
K0 = 150        # Default search turn rate
K1 = -100       # Turn rate based on puck angle
K2 = -150       # (Unused) Repulsion from other robots
K3 = 200        # Goal attraction weight
BASE_SPEED = 300
MAX_TURN_RATE = 100000000
SEARCH_TURN = 300
```

### Vision Settings

```python
PUCK_HSV = {
    "lower": np.array([100, 70, 50]),
    "upper": np.array([140, 255, 255])
}
MIN_PUCK_AREA = 384  # Adjustable by resolution
ERODE_ITER = 10
DILATE_ITER = 1
```

### ROI Settings

```python
ROI_TOP_WIDTH = 0.4
ROI_BOTTOM_WIDTH = 0.4
ROI_HEIGHT = 0.9
```

## Code Structure

- `ForagingController`: Main class encapsulating system logic.
  - `initialize_system()`: Hardware and sensor startup.
  - `detect_puck(frame)`: Vision-based puck detection.
  - `calculate_goal_attraction(distance)`: Adjusts heading toward goal.
  - `control_motors(...)`: Computes wheel speeds.
  - `draw_debug_info(...)`: Optional debug overlay.
  - `run()`: Main loop capturing frames, detecting pucks, adjusting movement, and optionally showing debug window.

## Dependencies

Install required libraries:

```bash
pip3 install numpy opencv-python
```

Additional requirements:

- `picamera`
- Custom modules: `Zumo`, `uwb_reader` (ensure these are in the working directory or Python path)

## Running the Program

Make sure your robot is connected and hardware components are properly installed. Then execute:

```bash
python3 forage.py
```

Press `q` to exit the debug window (if `SHOW_VIDEO` is enabled) or `Ctrl+C` to safely terminate.

## Notes

- Ensure UWB module is connected at the specified `UWB_PORT`.
- Tuning parameters like `K1`, `K3`, and `BASE_SPEED` may be adjusted for optimal performance depending on lighting, puck size, and environment.
