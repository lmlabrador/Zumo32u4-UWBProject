import serial
import time

def get_filtered_position(ser, num_readings=20):
    """
    Collect multiple UWB readings and return the filtered position.
    The expected UWB data format is: POS, x, y, z, quality
    The 'lep' command is sent only once to start continuous streaming.
    """
    positions = []

    # Send the 'lep' command only once to start continuous streaming
    ser.write(b"\n\n")
    time.sleep(1.0)

    ser.write(b"lep\n")
    time.sleep(0.5)  # Wait for the module to start streaming

    for _ in range(num_readings):
        # Read a line from the continuous stream
        data = ser.readline().decode().strip()
        print(f"Raw UWB data: {data}")  # Debugging: Print raw data

        # Parse the data
        try:
            parts = data.split(',')
            if parts[0] == "POS" and len(parts) >= 3:
                x = float(parts[1])  # Extract x coordinate
                y = float(parts[2])  # Extract y coordinate
                positions.append((x, y))  # Store (x, y) position
        except (ValueError, IndexError):
            print(f"Failed to parse UWB data: {data}")
            continue

    # Check if we have valid readings
    if not positions:
        print("No valid UWB readings collected.")
        return (None, None)

    # Calculate the average position
    avg_x = sum(p[0] for p in positions) / len(positions)
    avg_y = sum(p[1] for p in positions) / len(positions)
    print(f"Average Position: ({avg_x}, {avg_y})")
    return (avg_x, avg_y)
