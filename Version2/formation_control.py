import math
from config import FORMATION_DISTANCE, COLLISION_THRESHOLD

def calculate_formation_position(leader_position, follower_id, formation_mode, num_robots):
    """
    Calculate the target position for a follower based on the leader's position and formation mode.
    """
    if formation_mode == "single":
        return leader_position  # Single robot acts as the leader
    elif formation_mode == "line":
        if follower_id == "robot_2":
            return (leader_position[0], leader_position[1] + FORMATION_DISTANCE)
        else:
            return leader_position
    elif formation_mode == "triangle":
        if follower_id == "robot_2":
            return (leader_position[0] - FORMATION_DISTANCE, leader_position[1] + FORMATION_DISTANCE)
        elif follower_id == "robot_3":
            return (leader_position[0] + FORMATION_DISTANCE, leader_position[1] + FORMATION_DISTANCE)
        else:
            return leader_position
    elif formation_mode == "diamond":
        if follower_id == "robot_2":
            return (leader_position[0], leader_position[1] + FORMATION_DISTANCE)
        elif follower_id == "robot_3":
            return (leader_position[0] - FORMATION_DISTANCE, leader_position[1])
        elif follower_id == "robot_4":
            return (leader_position[0], leader_position[1] - FORMATION_DISTANCE)
        else:
            return leader_position
    elif formation_mode == "circle":
        angle = 2 * math.pi / (num_robots - 1)  # Divide the circle equally among followers
        follower_index = int(follower_id.split("_")[1]) - 2  # robot_2 -> index 0, robot_3 -> index 1, etc.
        x = leader_position[0] + FORMATION_DISTANCE * math.cos(angle * follower_index)
        y = leader_position[1] + FORMATION_DISTANCE * math.sin(angle * follower_index)
        return (x, y)
    else:
        return leader_position  # Default to leader position

def avoid_collision(current_position, other_positions):
    """
    Adjust the target position to avoid collisions with other robots.
    """
    for other_position in other_positions:
        dx = other_position[0] - current_position[0]
        dy = other_position[1] - current_position[1]
        distance = math.sqrt(dx**2 + dy**2)
        if distance < COLLISION_THRESHOLD:
            # Move away from the other robot
            return (current_position[0] - dx, current_position[1] - dy)
    return current_position
