import paho.mqtt.client as mqtt
import json

# MQTT Settings
MQTT_BROKER = "192.168.1.5"  # Replace with RPi/Win IP
MQTT_PORT = 1883
TOPIC_POSITION = "sensors/position"
TOPIC_NUMBERS = "data/numbers"
TOPIC_LETTERS = "data/text"

def on_connect(client, userdata, flags, rc):
    print(f"Connected (Code: {rc})")
    client.subscribe([(TOPIC_POSITION, 0), (TOPIC_NUMBERS, 0), (TOPIC_LETTERS, 0)])

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == TOPIC_POSITION:
        data = json.loads(payload)
        print(f"Position: X={data['x']}, Y={data['y']}, Z={data['z']}")
    elif topic == TOPIC_NUMBERS:
        print(f"Number received: {payload}")
    elif topic == TOPIC_LETTERS:
        print(f"Text received: {payload}")

def listen():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Listening for messages...")
    client.loop_forever()

if __name__ == "__main__":
    listen()