# import asyncio
# import json
# import math
# import paho.mqtt.client as mqtt
# from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_LEADER_POSITION, MQTT_TOPIC_FOLLOWER_POSITION, MQTT_TOPIC_TARGET, MQTT_TOPIC_FORMATION

# class SwarmController:
#     def __init__(self):
#         self.client = mqtt.Client()
#         self.client.on_connect = self.on_connect
#         self.client.on_message = self.on_message

#         self.leader_position = None
#         self.follower_positions = {}
#         self.target_position = None
#         self.robots_reached_target = set()
#         self.num_robots = 0
#         self.formation_mode = "line"
#         self.robot_headings = {}

#     def on_connect(self, client, userdata, flags, rc):
#         print(f"Connected to MQTT broker with result code {rc}")
#         if rc == 0:
#             self.client.subscribe(MQTT_TOPIC_FOLLOWER_POSITION)
#             print(f"Subscribed to topic: {MQTT_TOPIC_FOLLOWER_POSITION}")
#         else:
#             print(f"Failed to connect to MQTT broker. Result code: {rc}")

#     def on_message(self, client, userdata, msg):
#         try:
#             payload = json.loads(msg.payload.decode("utf-8"))
#             print(f"Received message on topic {msg.topic}: {payload}")

#             if msg.topic == MQTT_TOPIC_FOLLOWER_POSITION:
#                 self.follower_positions[payload["id"]] = (payload["x"], payload["y"])
#                 self.robot_headings[payload["id"]] = payload["heading"]
#                 print(f"Updated positions: {self.follower_positions}")
#         except json.JSONDecodeError as e:
#             print(f"Failed to decode JSON payload: {e}")

#     async def assign_roles(self):
#         """Assign roles (leader/follower) and send target positions."""
#         if self.target_position:
#             # Assign the closest robot as the leader
#             closest_robot = None
#             min_distance = float('inf')
#             for robot_id, position in self.follower_positions.items():
#                 distance = self.calculate_distance(position, self.target_position)
#                 if distance < min_distance:
#                     min_distance = distance
#                     closest_robot = robot_id

#             if closest_robot:
#                 # Assign roles
#                 roles = {robot_id: "follower" for robot_id in self.follower_positions.keys() if robot_id != closest_robot}
#                 roles[closest_robot] = "leader"
#                 print(f"Assigned roles: {roles}")

#                 # Publish roles to swarm/formation
#                 self.client.publish(MQTT_TOPIC_FORMATION, json.dumps({
#                     "mode": self.get_formation_mode(),
#                     "leader": closest_robot,
#                     "roles": roles
#                 }))
#                 print(f"Sent roles to {MQTT_TOPIC_FORMATION}")

#                 # Calculate and publish target positions for each robot
#                 for robot_id, role in roles.items():
#                     if role == "leader":
#                         # Leader gets the original target position
#                         target = self.target_position
#                     else:
#                         # Followers get adjusted target positions to avoid collisions
#                         target = self.calculate_formation_position(robot_id, self.target_position, self.follower_positions)

#                     # Publish target position to the robot
#                     self.client.publish(f"swarm/target/{robot_id}", json.dumps({"x": target[0], "y": target[1]}))
#                     print(f"Sent target position to robot {robot_id}: {target}")

#     def calculate_distance(self, pos1, pos2):
#         """Calculate the Euclidean distance between two positions."""
#         return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

#     def calculate_formation_position(self, robot_id, target_position, follower_positions):
#         """Calculate the target position for a follower based on the formation."""
#         # Example: Offset followers by 0.2 meters in the x-direction
#         if robot_id in follower_positions:
#             return (target_position[0] + 0.2, target_position[1])
#         return target_position

#     def get_formation_mode(self):
#         """Determine the formation mode based on the number of robots."""
#         if self.num_robots == 2:
#             return "line"
#         elif self.num_robots == 3:
#             return "triangle"
#         elif self.num_robots == 4:
#             return "diamond"
#         elif self.num_robots >= 5:
#             return "circle"
#         else:
#             return "single"

#     async def run(self):
#         """Main loop for the swarm controller."""
#         self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         self.client.loop_start()

#         # Wait for all robots to report initial positions
#         while len(self.follower_positions) < self.num_robots:
#             print(f"Waiting for robots to report positions... ({len(self.follower_positions)}/{self.num_robots})")
#             await asyncio.sleep(1)

#         # Assign roles and send target positions
#         await self.assign_roles()

#         # Keep the script running
#         while True:
#             await asyncio.sleep(1)

# if __name__ == "__main__":
#     controller = SwarmController()
#     controller.num_robots = int(input("Enter the number of robots: "))

#     # Set target position
#     target_x = float(input("Enter target X coordinate: "))
#     target_y = float(input("Enter target Y coordinate: "))
#     controller.target_position = (target_x, target_y)

#     asyncio.run(controller.run())
    


######################################

import asyncio
import json
import math
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_LEADER_POSITION, MQTT_TOPIC_FOLLOWER_POSITION, MQTT_TOPIC_TARGET, MQTT_TOPIC_FORMATION

class SwarmController:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.leader_position = None
        self.follower_positions = {}
        self.target_position = None
        self.robots_reached_target = set()
        self.num_robots = 0
        self.formation_mode = "single"
        self.robot_headings = {}
        self.formation_spacing = 0.2  # meters between robots in formation

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        if rc == 0:
            self.client.subscribe(MQTT_TOPIC_FOLLOWER_POSITION)
            print(f"Subscribed to topic: {MQTT_TOPIC_FOLLOWER_POSITION}")
        else:
            print(f"Failed to connect to MQTT broker. Result code: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            print(f"Received message on topic {msg.topic}: {payload}")

            if msg.topic == MQTT_TOPIC_FOLLOWER_POSITION:
                self.follower_positions[payload["id"]] = (payload["x"], payload["y"])
                self.robot_headings[payload["id"]] = payload["heading"]
                print(f"Updated positions: {self.follower_positions}")
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON payload: {e}")

    async def assign_roles(self):
        """Assign roles (leader/follower) and send target positions."""
        if self.target_position:
            # Assign the closest robot as the leader
            closest_robot = None
            min_distance = float('inf')
            for robot_id, position in self.follower_positions.items():
                distance = self.calculate_distance(position, self.target_position)
                if distance < min_distance:
                    min_distance = distance
                    closest_robot = robot_id

            if closest_robot:
                # Assign roles
                roles = {robot_id: "follower" for robot_id in self.follower_positions.keys() if robot_id != closest_robot}
                roles[closest_robot] = "leader"
                print(f"Assigned roles: {roles}")

                # Publish roles to swarm/formation
                self.client.publish(MQTT_TOPIC_FORMATION, json.dumps({
                    "mode": self.get_formation_mode(),
                    "leader": closest_robot,
                    "roles": roles
                }))
                print(f"Sent roles to {MQTT_TOPIC_FORMATION}")

                # Calculate and publish target positions for each robot
                for robot_id, role in roles.items():
                    if role == "leader":
                        # Leader gets the original target position
                        target = self.target_position
                    else:
                        # Followers get positions based on formation
                        target = self.calculate_formation_position(robot_id, closest_robot, self.target_position)

                    # Publish target position to the robot
                    self.client.publish(f"swarm/target/{robot_id}", json.dumps({"x": target[0], "y": target[1]}))
                    print(f"Sent target position to robot {robot_id}: {target}")

    def calculate_distance(self, pos1, pos2):
        """Calculate the Euclidean distance between two positions."""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def calculate_formation_position(self, robot_id, leader_id, target_position):
        """Calculate the target position for a follower based on the formation."""
        robot_index = sorted(self.follower_positions.keys()).index(robot_id)
        leader_index = sorted(self.follower_positions.keys()).index(leader_id)
        
        # Calculate position based on formation mode
        if self.formation_mode == "single":
            return target_position
            
        elif self.formation_mode == "line":
            # Line formation: robots in a horizontal line
            offset = (robot_index - leader_index) * self.formation_spacing
            return (target_position[0] + offset, target_position[1])
            
        elif self.formation_mode == "triangle":
            # Triangle formation (1 leader, 2 followers forming a triangle)
            if robot_index == leader_index:
                return target_position
            elif robot_index == (leader_index + 1) % self.num_robots:
                return (target_position[0] - self.formation_spacing, 
                        target_position[1] - self.formation_spacing)
            else:
                return (target_position[0] + self.formation_spacing, 
                        target_position[1] - self.formation_spacing)
                        
        elif self.formation_mode == "square":
            # Square formation (leader at one corner)
            square_positions = [
                target_position,  # Leader position (bottom-left)
                (target_position[0] + self.formation_spacing, target_position[1]),  # bottom-right
                (target_position[0], target_position[1] + self.formation_spacing),  # top-left
                (target_position[0] + self.formation_spacing, target_position[1] + self.formation_spacing)  # top-right
            ]
            return square_positions[robot_index % 4]
            
        else:
            # Default to circle formation for 5+ robots
            angle = 2 * math.pi * robot_index / self.num_robots
            radius = self.formation_spacing * (self.num_robots / (2 * math.pi))
            return (
                target_position[0] + radius * math.cos(angle),
                target_position[1] + radius * math.sin(angle)
            )

    def get_formation_mode(self):
        """Determine the formation mode based on the number of robots."""
        if self.num_robots == 1:
            self.formation_mode = "single"
        elif self.num_robots == 2:
            self.formation_mode = "line"
        elif self.num_robots == 3:
            self.formation_mode = "triangle"
        elif self.num_robots == 4:
            self.formation_mode = "square"
        elif self.num_robots >= 5:
            self.formation_mode = "circle"
        return self.formation_mode

    async def run(self):
        """Main loop for the swarm controller."""
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

        # Wait for all robots to report initial positions
        while len(self.follower_positions) < self.num_robots:
            print(f"Waiting for robots to report positions... ({len(self.follower_positions)}/{self.num_robots})")
            await asyncio.sleep(1)

        # Assign roles and send target positions
        await self.assign_roles()

        # Keep the script running
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    controller = SwarmController()
    controller.num_robots = int(input("Enter the number of robots: "))

    # Set target position
    target_x = float(input("Enter target X coordinate: "))
    target_y = float(input("Enter target Y coordinate: "))
    controller.target_position = (target_x, target_y)

    asyncio.run(controller.run())