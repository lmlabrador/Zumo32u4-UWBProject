import time
import json
import threading
import math
import paho.mqtt.client as mqtt
from uwb_reader import UWBReader
from Zumo import Zumo
from navigation import calculate_turn_angle, is_within_target, normalize_angle, calculate_heading
from config import ROBOT_ID, MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_LEADER_POSITION, MQTT_TOPIC_FOLLOWER_POSITION, MQTT_TOPIC_TARGET, MQTT_TOPIC_FORMATION

# Constants for movement
MOTOR_SPEED_FORWARD = 350
MOTOR_SPEED_TURN = 350
ANGLE_TOLERANCE = math.radians(10)
TARGET_TOLERANCE = 0.1  # Target proximity tolerance in meters
Kp = 0.2  # Proportional constant for straight-line corrections

# Constants from calibration
DISTANCE_TO_ENCODER_DELTA = 10176
TURN_ANGLE_TO_ENCODER_DELTA = 432.2648

# Global variables for MQTT communication
target_position = None
role = "follower"
leader_position = None
follower_positions = {}
formation_mode = "line"
num_robots = 1


def turn_in_place(zumo, motor_speed, desired_turn_angle):
    """Turn the robot in place using encoder-based logic."""
    assert(motor_speed > 0 and motor_speed <= 400)

    # Reset encoders
    zumo.reset_encoders()
    right_count, left_count = 0, 0

    # Compute the desired encoder count for the turn
    desired_right_count = abs(desired_turn_angle) * TURN_ANGLE_TO_ENCODER_DELTA

    if desired_turn_angle > 0:
        # Turn right
        zumo.send_speeds(-motor_speed, motor_speed)
        print(f"Turning right at speed {motor_speed}")
        while right_count < desired_right_count:
            left_count, right_count = zumo.get_encoders()
    else:
        # Turn left
        zumo.send_speeds(motor_speed, -motor_speed)
        print(f"Turning left at speed {motor_speed}")
        while left_count < desired_right_count:
            left_count, right_count = zumo.get_encoders()

    # Stop the robot after turning
    zumo.send_speeds(0, 0)
    print("Turn complete.")

def move_forward(zumo, distance, base_speed=MOTOR_SPEED_FORWARD):
    """Move the robot forward with proportional control to keep it straight."""
    # Reset encoders
    zumo.reset_encoders()
    left_count, right_count = 0, 0

    # Compute the desired encoder count for the distance
    desired_count = distance * DISTANCE_TO_ENCODER_DELTA

    print(f"Moving forward by {distance:.2f} meters at speed {base_speed}")
    while left_count < desired_count or right_count < desired_count:
        # Get current encoder counts
        left_count, right_count = zumo.get_encoders()

        # Calculate the error
        error = left_count - right_count

        # Adjust motor speeds using proportional control
        left_speed = base_speed - (Kp * error)
        right_speed = base_speed + (Kp * error)

        # Ensure motor speeds are within valid range
        left_speed = max(0, min(400, left_speed))
        right_speed = max(0, min(400, right_speed))

        # Send adjusted speeds to the motors
        zumo.send_speeds(left_speed, right_speed)

    # Stop the robot after moving
    zumo.send_speeds(0, 0)
    print("Move complete.")



def publish_position(client, position, heading):
    """Publish the robot's current position and heading."""
    payload = {
        "id": ROBOT_ID,
        "x": position[0],
        "y": position[1],
        "heading": heading
    }
    client.publish(MQTT_TOPIC_FOLLOWER_POSITION, json.dumps(payload))
    print(f"Published position: {payload}")



def subscribe_to_target(client):
    """Subscribe to the target position topic and wait for a valid message."""
    global target_position

    def on_message(client, userdata, msg):
        global target_position
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            print(f"Received message on topic {msg.topic}: {payload}")

            # Validate the message format
            if "x" in payload and "y" in payload:
                target_position = (float(payload["x"]), float(payload["y"]))
                print(f"Updated target position: {target_position}")
            else:
                print("Invalid message format: 'x' and 'y' keys are required.")
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON payload: {e}")
        except ValueError as e:
            print(f"Invalid value in payload: {e}")

    client.on_message = on_message
    client.subscribe(f"swarm/target/{ROBOT_ID}")
    print(f"Subscribed to topic: swarm/target/{ROBOT_ID}")

    # Wait for a valid target position
    while target_position is None:
        print("Waiting for target position...")
        client.loop(timeout=1.0)  # Process MQTT messages

    # Disconnect after receiving a valid target position
    client.disconnect()
    print("Disconnected after receiving target position.")

def main():
    # Initialize UWB reader and Zumo robot
    uwb_reader = UWBReader()
    if not uwb_reader.start():
        return
    zumo = Zumo()

    # Get initial position and heading
    previous_pos = (None, None)
    while True:
        pos = uwb_reader.get_latest_position()
        if pos != (None, None):
            previous_pos = pos
            print(f"Initial position acquired: {previous_pos}")
            break
        time.sleep(0.1)

    # Move forward to establish heading
    initial_move_distance = 0.4
    print(f"Performing an initial move of {initial_move_distance} m to establish heading.")
    move_forward(zumo, initial_move_distance)

    # Compute initial heading
    time.sleep(0.2)
    current_pos = uwb_reader.get_latest_position()
    if current_pos == (None, None):
        print("Could not get position after initial move.")
        uwb_reader.stop()
        return
    zumo.heading = calculate_heading(current_pos, previous_pos)
    print(f"Initial heading: {math.degrees(zumo.heading):.2f} degrees")

    # Publish initial position
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    publish_position(client, current_pos, zumo.heading)
    client.disconnect()
    print("Disconnected after publishing initial position.")

    # Subscribe to target position
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    subscribe_to_target(client)

    # Main navigation loop
    try:
        while True:
            current_pos = uwb_reader.get_latest_position()
            if current_pos == (None, None):
                print("No valid UWB data received. Retrying...")
                time.sleep(0.1)
                continue

            print(f"Current position: {current_pos}")
            print(f"Target position: {target_position}, Tolerance: {TARGET_TOLERANCE}")

            if is_within_target(current_pos, target_position, TARGET_TOLERANCE):
                print("Target position reached!")
                break

            # Calculate target angle and move
            dx_target = target_position[0] - current_pos[0]
            dy_target = target_position[1] - current_pos[1]
            theta_target = math.atan2(dy_target, dx_target)
            gamma = normalize_angle(theta_target - zumo.heading)

            print(f"Target angle: {math.degrees(theta_target):.2f} degrees")
            print(f"Relative turning angle (gamma): {math.degrees(gamma):.2f} degrees")

            if abs(gamma) > ANGLE_TOLERANCE:
                print("Turning to face the target.")
                turn_in_place(zumo, MOTOR_SPEED_TURN, gamma)
                zumo.heading = normalize_angle(zumo.heading + gamma)
            else:
                distance_to_target = math.sqrt(dx_target**2 + dy_target**2)
                print(f"Moving forward by {distance_to_target:.2f} meters.")
                move_forward(zumo, distance=distance_to_target)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        zumo.send_speeds(0, 0)
        uwb_reader.stop()


if __name__ == "__main__":
    main()
