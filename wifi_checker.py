import subprocess
import re
import time
import json

INTERFACE = "wlan1"


def get_available_networks():
    result = subprocess.run(
        ["nmcli", "--fields", "SSID,SIGNAL", "device", "wifi", "list"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    output = result.stdout.strip()
    matches = re.findall(r"(\S+)\s+(\d+)", output)

    available_networks = []
    for ssid, signal in matches:
        if ssid == "--":
            continue
        if int(signal) > 75:
            continue

        available_networks.append(ssid)

    return available_networks


def get_connected_network():
    # Run the nmcli command to get the connected Wi-Fi SSID
    result = subprocess.run(
        ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
        capture_output=True,
        text=True,
    )
    # Parse the output to find the active connection
    for line in result.stdout.splitlines():
        active, ssid = line.split(":", 1)
        if active == "yes":
            return ssid

    return None


def connect_to_network(ssid, password=None, interface="wlan0"):
    # Build the command
    command = ["nmcli", "dev", "wifi", "connect", ssid, "ifname", interface]
    if password:
        command.extend(["password", password])

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Check for success or failure
    if result.returncode == 0:
        print(f"Successfully connected to {ssid}.")
    else:
        print(f"Failed to connect to {ssid}.\nError: {result.stderr.strip()}")


def main():
    while True:
        try:
            connected = get_connected_network()
            if connected:
                print(f"Already connected to {connected}.")
            else:
                print("No active connection. Scanning for available networks...")
                available = get_available_networks()
                stored = json.load(open("networks.json"))

                for ssid in available:
                    if ssid in stored:
                        print(f"Attempting to connect to {ssid}...")
                        connect_to_network(
                            ssid, password=stored[ssid], interface=INTERFACE
                        )
                        break
                else:
                    print("No preferred networks found.")
        except Exception as ex:
            print(f"An error occurred: {ex}")

        time.sleep(300)  # Wait for 5 minutes before checking again


if __name__ == "__main__":
    main()
