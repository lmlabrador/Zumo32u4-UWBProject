import paho.mqtt.client as mqtt
import json

# MQTT Settings
MQTT_BROKER = "192.168.1.5"  # Replace with RPi/Win IP
MQTT_PORT = 1883
TOPIC_POSITION = "sensors/position"
TOPIC_NUMBERS = "data/numbers"
TOPIC_LETTERS = "data/text"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to broker (Code: {rc})")

def send_data():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    while True:
        print("\nChoose data type to send:")
        print("1. Position (x,y,z)")
        print("2. Number")
        print("3. Text")
        print("4. Exit")

        choice = input("Enter choice (1-4): ")

        if choice == "1":
            x = input("Enter X: ")
            y = input("Enter Y: ")
            z = input("Enter Z: ")
            data = {"x": x, "y": y, "z": z}
            client.publish(TOPIC_POSITION, json.dumps(data))
            print(f"Sent position: {data}")

        elif choice == "2":
            num = input("Enter a number: ")
            client.publish(TOPIC_NUMBERS, num)
            print(f"Sent number: {num}")

        elif choice == "3":
            text = input("Enter text: ")
            client.publish(TOPIC_LETTERS, text)
            print(f"Sent text: {text}")

        elif choice == "4":
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    send_data()