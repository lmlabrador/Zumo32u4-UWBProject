
# Detailed MQTT Setup Guide: Raspberry Pi 4B & Windows Laptop
**Using Mosquitto Broker for Position Data, Numbers, and Text Messages**

## Table of Contents
- Prerequisites
- Step 1: Install Mosquitto Broker
  - On Raspberry Pi (RPi4B)
  - On Windows
- Step 2: Configure Firewalls
  - Windows Firewall Setup
  - Raspberry Pi Firewall (UFW)
- Step 3: Test MQTT Communication
  - Test 1: Windows → Raspberry Pi
  - Test 2: Raspberry Pi → Windows
- Step 4: Python MQTT Scripts
  - Publisher Script (Send Data)
  - Subscriber Script (Receive Data)
- Running the System
- Troubleshooting

## Prerequisites
**For Raspberry Pi 4B:**
- Raspberry Pi OS (latest)
- Python 3 (`sudo apt install python3 python3-pip`)
- Internet connection (Wi-Fi/Ethernet)

**For Windows Laptop:**
- Python 3 (Download from python.org)
- Admin rights (for firewall & Mosquitto installation)

## Step 1: Install Mosquitto Broker

### On Raspberry Pi (RPi4B)
Update system & install Mosquitto:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install mosquitto mosquitto-clients -y
```

Enable and start Mosquitto service:
```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Check if it's running:
```bash
sudo systemctl status mosquitto
```
(Should show active (running))

Install Python MQTT library:
```bash
pip install paho-mqtt
```

### On Windows
Download Mosquitto Installer:

- Go to [mosquitto.org/download](https://mosquitto.org/download)
- Download `mosquitto-x.x.x-install-windows-x64.exe`

Run Installer with:
- Mosquitto Broker
- Service Install
- MQTT Client Utilities

Start Mosquitto Service (Admin CMD):
```cmd
net start mosquitto
```

Install Python MQTT Library:
```cmd
pip install paho-mqtt
```

## Step 2: Configure Firewalls

### Windows Firewall Setup
1. Open Windows Defender Firewall with Advanced Security
2. Add Inbound Rule:
   - Port: 1883 (TCP)
   - Action: Allow
   - Scope: Private & Public
   - Name: MQTT Broker

(Optional) Repeat for Outbound Rule if needed.

### Raspberry Pi Firewall (UFW)
Install UFW (if not installed):
```bash
sudo apt install ufw
```

Allow MQTT & SSH:
```bash
sudo ufw allow 1883
sudo ufw allow 22
```

Enable firewall:
```bash
sudo ufw enable
sudo ufw status
```

## Step 3: Test MQTT Communication

### Test 1: Windows → Raspberry Pi

On RPi4 (Subscriber):
```bash
mosquitto_sub -h localhost -t "test/topic" -v
```

On Windows (Publisher):
```cmd
mosquitto_pub -h <RPi_IP> -t "test/topic" -m "Hello from Windows!"
```
(Replace `<RPi_IP>` with Raspberry Pi's IP)

Expected: Message appears on RPi terminal.

### Test 2: Raspberry Pi → Windows

On Windows (Subscriber):
```cmd
mosquitto_sub -h localhost -t "test/topic" -v
```

On RPi4 (Publisher):
```bash
mosquitto_pub -h <Windows_IP> -t "test/topic" -m "Hello from RPi4!"
```
(Replace `<Windows_IP>` with laptop's IP)

Expected: Message appears on Windows terminal.

## Step 4: Python MQTT Scripts

### Publisher Script (Send Data)
(Run on either device to send data)

See: `mqtt_publisher.py`

### Subscriber Script (Receive Data)
(Run on either device to receive data)

See: `mqtt_subscriber.py`

## Running the System
- Run Subscriber First (on either device).
- Run Publisher (on the other device).
- Choose data type (Position, Number, Text).
- See received data in Subscriber terminal.

## Troubleshooting

**Connection Issues?**
- Check broker IP (`ifconfig` on RPi, `ipconfig` on Windows).
- Verify Mosquitto is running (`sudo systemctl status mosquitto`).
- Disable firewalls temporarily for testing.

**No Messages?**
- Ensure both devices are on the same network.
- Check topic names match in Publisher/Subscriber.

**Python Errors?**
- Ensure `paho-mqtt` is installed (`pip install paho-mqtt`).
