# Swarm Robotics Project - Zumo Robot Navigation

## Overview

This project implements a swarm robotics system where multiple Zumo robots navigate to target positions using UWB positioning and MQTT communication. The system consists of:

1. A **central swarm controller** running on a laptop (MQTT broker)
2. **Individual robot controllers** running on Raspberry Pis connected to each Zumo robot

## System Architecture

[Laptop (Broker)]
|
|-- MQTT Communication
|
[Robot 1 (RPi)] -- Zumo Robot
[Robot 2 (RPi)] -- Zumo Robot
...
[Robot N (RPi)] -- Zumo Robot

## Hardware Requirements

- Zumo robot with encoders
- Raspberry Pi (per robot)
- UWB positioning module (e.g., Decawave DWM1001)
- Laptop running the swarm controller

## Software Requirements

- Python 3.x
- Required Python packages:
  - paho-mqtt
  - pyserial
  - numpy

## Setup Instructions

### 1. Swarm Controller (Laptop)

Install Python 3.x and required packages:

    pip install paho-mqtt asyncio

Run the swarm controller:

    python swarm_controller.py

When prompted, enter:

- Number of robots in the swarm
- Target coordinates (x, y)

### 2. Robot Controllers (Raspberry Pi)

For each robot:

Install dependencies:

    pip install paho-mqtt pyserial

Configure the robot by editing config.py:

    ROBOT_ID = "robot_X"  # Unique ID for each robot (e.g., robot_1, robot_2)
    MQTT_BROKER = "192.168.1.5"  # IP address of the laptop running the swarm controller

Connect the hardware:

- Ensure UWB module is connected to /dev/ttyACM1
- Zumo robot is connected to /dev/ttyACM0

Run the main program:

    python main.py

#### Calibration

Before running the main program, calibrate each robot's movement:

Run the calibration script:

    python calibrate.py

Note the calibration constants printed at the end.

Update these constants in main.py:

    DISTANCE_TO_ENCODER_DELTA = [your_calibrated_value]  # Typically around 10176
    TURN_ANGLE_TO_ENCODER_DELTA = [your_calibrated_value]  # Typically around 432.2648

## Key Features

- Precise Movement: Encoder-based movement with PID control
- UWB Positioning: Accurate position tracking
- Formation Control: Supports multiple formation patterns:
  - Single
  - Line
  - Triangle
  - Square
  - Circle
- Collision Avoidance: Robots maintain safe distances
- Dynamic Role Assignment: Automatic leader/follower assignment

## File Structure

| File                | Purpose                                        |
| ------------------- | ---------------------------------------------- |
| main.py             | Main robot control program                     |
| calibrate.py        | Robot movement calibration                     |
| swarm_controller.py | Central swarm coordination                     |
| Zumo.py             | Zumo robot interface                           |
| SerialGateway.py    | Serial communication handler                   |
| uwb_reader.py       | UWB position reader                            |
| navigation.py       | Navigation utilities                           |
| config.py           | Configuration file (per robot)                 |
| test.py             | Testing script for individual robot navigation |

## MQTT Topics

| Topic                   | Purpose                         |
| ----------------------- | ------------------------------- |
| swarm/leader_position   | Leader robot position updates   |
| swarm/follower_position | Follower robot position updates |
| swarm/target            | Global target position          |
| swarm/formation         | Formation configuration updates |

## Troubleshooting

### Common Issues

## UWB Not Connecting

- Check physical connections
- Verify the correct port is set in `uwb_reader.py`
- Try resetting the UWB module
- If you're on a fresh boot, run the following in your terminal to get consistent readings from the UWB:

  screen /dev/ttyACM1 115200
  Press Enter twice quickly (or until you see dwm> on the terminal)

Then run:

    lep

If successful, you will see position readings in this format:

    POS,x_cord,y_cord,z_cord

To exit the screen session:
Press:

    Ctrl + A, then K

(you may need to repeat this constantly)

When prompted with "Kill this window":

    press Y to confir

**MQTT connection issues:**

- Verify broker IP in config.py
- Check network connectivity
- Ensure firewall allows MQTT traffic (port 1883)

**Robot not moving straight:**

- Re-run calibration
- Adjust Kp constant in main.py

**Encoder values not updating:**

- Check Zumo robot serial connection
- Verify baud rate (115200)
- Ensure ZumoSerial sketch is properly uploaded

## Development Notes

- The system uses a proportional controller (P-term only) for movement correction
- UWB positioning updates at approximately 10Hz
- Each robot maintains its own heading estimate
- Formation spacing is configurable via formation_spacing in swarm_controller.py
