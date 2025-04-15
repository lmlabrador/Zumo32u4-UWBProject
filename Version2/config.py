ROBOT_ID = "robot_1"

# MQTT Configuration
MQTT_BROKER = "192.168.1.5"  # Replace with your MQTT broker IP
MQTT_PORT = 1883
MQTT_TOPIC_LEADER_POSITION = "swarm/leader/position"
MQTT_TOPIC_FOLLOWER_POSITION = "swarm/follower/position"
MQTT_TOPIC_TARGET = "swarm/target"
MQTT_TOPIC_FORMATION = "swarm/formation"
MQTT_TOPIC_ROBOT_COUNT = "swarm/robot_count"

# Formation Parameters
FORMATION_DISTANCE = 0.3  # Distance between robots in meters (12 inches)
COLLISION_THRESHOLD = 0.1  # Minimum distance to avoid collisions (4 inches)

# Movement Constants
MOTOR_SPEED_FORWARD = 400
MOTOR_SPEED_TURN = 350
ANGLE_TOLERANCE = 0.174533  # 10 degrees in radians
TARGET_TOLERANCE = 0.1  # Target proximity tolerance in meters
Kp = 0.2  # Proportional constant for straight-line corrections

