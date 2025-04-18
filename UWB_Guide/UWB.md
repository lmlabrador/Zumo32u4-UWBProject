# UWB Troubleshooting Guide

This guide helps troubleshoot issues when the UWB module is not connecting or providing readings.

## 1. Check Physical Connections

- Ensure that all cables are properly connected.
- Confirm the UWB module is receiving power.

## 2. Verify the Port in Code

- Open the file `uwb_reader.py`.
- Check that the port specified matches the correct one (e.g., `/dev/ttyACM1` or `/dev/ttyUSB0`).

## 3. Reset the UWB Module

- Try power cycling or pressing the reset button on the UWB module.
- Wait a few seconds before trying again.

## 4. Initialize UWB After Boot

On a fresh boot, follow these steps in your terminal to get consistent readings from the UWB:

```bash
screen /dev/ttyACM1 115200
```

Press Enter twice quickly or until you see the dwm> prompt.

Then, type the following command:

```bash
lep
```

If successful, you will see position readings in this format:

```
POS,x_cord,y_cord,z_cord
```

## 5. Exiting the Screen Session

To exit the screen session:

Press Ctrl + A, then K

May need to press it fast over and over again

When prompted with "Kill this window", press Y to confirm

Note: You may need to repeat this initialization every time you reboot the system.
