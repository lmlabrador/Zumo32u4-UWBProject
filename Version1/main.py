import time
import serial
import argparse
import math
from uwb_reader import get_filtered_position
from Zumo import Zumo
from navigation import calculate_turn_angle, is_within_target, normalize_angle

# Fine-tuned constants from calibration
DISTANCE_TO_ENCODER_DELTA = 10364 * 0.9746  # Adjusted for 1 inch over
TURN_ANGLE_TO_ENCODER_DELTA = 508.66 * 1.07  # Adjusted for 5-10 degrees under
Kp = 0.15  # Increased to reduce drift

# Constants for encoder-based turning
MOTOR_SPEED = 350  # Calibrated speed
ANGLE_TOLERANCE = math.radians(15)  # 15 degrees in radians

def turn_in_place(zumo, motor_speed, desired_turn_angle):
    """Turn the robot in place using encoder-based logic."""
    assert(motor_speed > 0 and motor_speed <= 400)

    # Reset encoders
    zumo.reset_encoders()
    right_count, left_count  = 0, 0

    # Compute the desired encoder count for the turn
    desired_right_count = abs(desired_turn_angle) * TURN_ANGLE_TO_ENCODER_DELTA
#    print(f"Desired encoder count: {desired_right_count}")

    if desired_turn_angle > 0:
        # Turn right
        zumo.send_speeds(-motor_speed, motor_speed)
        while right_count < desired_right_count:
            left_count, right_count = zumo.get_encoders()
 #           print(f"Encoder counts: Left={left_count}, Right={right_count}")
    else:
        # Turn left
        zumo.send_speeds(motor_speed, -motor_speed)
        while left_count < desired_right_count:
            left_count, right_count = zumo.get_encoders()
  #          print(f"Encoder counts: Left={left_count}, Right={right_count}")

    # Stop the robot after turning
    zumo.send_speeds(0, 0)

def move_forward(zumo, distance, base_speed=MOTOR_SPEED):
    """Move the robot forward with proportional control to keep it straight."""
    # Reset encoders
    zumo.reset_encoders()
    left_count, right_count = 0, 0

    # Compute the desired encoder count for the distance
    desired_count = distance * DISTANCE_TO_ENCODER_DELTA

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

   #     print(f"Encoder counts: Left={left_count}, Right={right_count}")
    #    print(f"Adjusted speeds: Left={left_speed}, Right={right_speed}")

    # Stop the robot after moving
    zumo.send_speeds(0, 0)

def main(target_x, target_y, tolerance=0.1, step_size=0.2):
    # Target position (x, y)
    TARGET_POS = (target_x, target_y)
    TARGET_TOLERANCE = tolerance

    # Open serial connection to UWB module
    ser = serial.Serial("/dev/ttyACM1", baudrate=115200, timeout=1)

    # Initialize Zumo robot
    zumo = Zumo()

    while True:
        # Get current position with filtering
        current_pos = get_filtered_position(ser, num_readings=20)
        if current_pos == (None, None):
            print("No valid UWB data received. Retrying...")
            time.sleep(1)
            continue

        print(f"Current position: {current_pos}")
        print(f"Target position: {TARGET_POS}, Tolerance: {TARGET_TOLERANCE}")

        # Check if within target proximity
        if is_within_target(current_pos, TARGET_POS, TARGET_TOLERANCE):
            print("Target position reached!")
            break

        # Calculate target angle
        dx_target = TARGET_POS[0] - current_pos[0]
        dy_target = TARGET_POS[1] - current_pos[1]
        theta_target = math.atan2(dy_target, dx_target)
   


        # Calculate relative turning angle (gamma)
        gamma = normalize_angle(theta_target - zumo.heading)

        print(f"Target angle: {math.degrees(theta_target):.2f} degrees")
        print(f"Relative turning angle (gamma): {math.degrees(gamma):.2f} degrees")

        # Turn the robot to face the target
        if abs(gamma) > ANGLE_TOLERANCE:
            print("Turning to face the target.")
            turn_in_place(zumo, MOTOR_SPEED, gamma)
            # Update the robot's heading
            zumo.heading = normalize_angle(zumo.heading + gamma)

        # Move the robot forward by a small step
        print(f"Moving forward by {step_size} meters.")
        move_forward(zumo, distance=step_size)

        time.sleep(1)  # Small delay before next iteration

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Navigate Zumo robot to a target position.")
    parser.add_argument("target_x", type=float, help="Target X coordinate")
    parser.add_argument("target_y", type=float, help="Target Y coordinate")
    parser.add_argument("--tolerance", type=float, default=0.1, help="Tolerance for reaching the target (default: 0.1)")
    parser.add_argument("--step_size", type=float, default=0.2, help="Step size for incremental movement (default: 0.2)")
    args = parser.parse_args()

    # Run the main function with the provided target position
    main(args.target_x, args.target_y, args.tolerance, args.step_size)
