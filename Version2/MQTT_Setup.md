# MQTT Server Setup with Mosquitto

This guide walks through installing Mosquitto, configuring it as an MQTT broker, and testing communication between a Windows PC and a Raspberry Pi 4. It also includes firewall tips for both systems.

---

## Step 1: Install Mosquitto

### On Windows

1. Download the installer from the official site:  
   [Mosquitto Windows Installer](https://mosquitto.org/download/)

   - Scroll down to the **Windows** section.
   - Download the latest `mosquitto-x.x.x-install-windows-x64.exe` file.

2. Run the installer and ensure these options are checked:

   - **Mosquitto Broker**
   - **Service Install**
   - **MQTT Client Utilities**

3. After installation:
   - Open `Command Prompt` as administrator
   - Start the Mosquitto service:
     ```bash
     net start mosquitto
     ```

### On Raspberry Pi (Raspbian/Debian-based)

1. Update your system:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install Mosquitto and client tools:

   ```bash
   sudo apt install mosquitto mosquitto-clients -y
   ```

3. Enable Mosquitto to start on boot:
   ```bash
   sudo systemctl enable mosquitto
   sudo systemctl start mosquitto
   ```

---

## Step 2: Test MQTT Connection

We’ll test by publishing a message from one device and subscribing on the other.

### From Windows → Raspberry Pi (as broker)

1. On **RPI4**, start a subscriber:

   ```bash
   mosquitto_sub -h localhost -t test/topic
   ```

2. On **Windows**, publish a message:
   ```bash
   mosquitto_pub -h <RPI4_IP_ADDRESS> -t test/topic -m "Hello from Windows!"
   ```

You should see the message appear on the Raspberry Pi terminal.

### From Raspberry Pi → Windows (as broker)

1. On **Windows**, open a `Command Prompt` and subscribe:

   ```bash
   mosquitto_sub -h localhost -t test/topic
   ```

2. On **RPI4**, publish:
   ```bash
   mosquitto_pub -h <WINDOWS_IP_ADDRESS> -t test/topic -m "Hello from RPI4!"
   ```

You should see the message on the Windows terminal.

---

## Step 3: Configure Firewalls

### Windows Firewall

1. Open **Windows Defender Firewall with Advanced Security**
2. Create an **Inbound Rule**:

   - **Port:** 1883 (TCP)
   - **Allow the connection**
   - Apply to **Private** and **Public** networks
   - Name it something like `MQTT Broker`

3. (Optional) Do the same for **Outbound Rule** if communication issues arise.

### Raspberry Pi

I had firewall issues with setting it up on Rpi4B

Here is what I did to fix it:

1. Install ufw:

   ```bash
   sudo apt install ufw
   ```

2. Allow MQTT port and SSH:

   ```bash
   sudo ufw allow 1883
   sudo ufw allow 22
   ```

3. Enable firewall:
   ```bash
   sudo ufw enable
   sudo ufw status
   ```

---

## Tips

- Use static IPs or hostnames for stability during testing.
- Ensure both devices are on the same network.
- MQTT default port is **1883** — make sure it's open on both ends.
- Use `mosquitto.conf` for advanced broker configurations (auth, logging, persistence).
- Use `-v` flag for verbose output during subscribe to see messages:
  ```bash
  mosquitto_sub -h localhost -t test/topic -v
  ```

---
