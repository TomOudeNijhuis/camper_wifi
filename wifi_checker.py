#!/usr/bin/env python3

import argparse
import subprocess
import re
import time
import json
import os
import logging

INTERFACE = "wlan1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    filename=os.path.join(SCRIPT_DIR, "wifi_checker.log"),
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)


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


def get_wifi_interfaces():
    result = subprocess.run(
        ["nmcli", "-t", "-f", "DEVICE,TYPE", "device"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    output = result.stdout.strip()
    interfaces = []
    for line in output.split("\n"):
        device, dev_type = line.split(":")
        if dev_type == "wifi":
            interfaces.append(device)
    return interfaces


def connect_to_network(ssid, password=None, interface=INTERFACE):
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


def get_stored_networks():
    networks_path = os.path.join(SCRIPT_DIR, "networks.json")

    return json.load(open(networks_path))


def run_watcher(interface):
    while True:
        try:
            connected = get_connected_network()
            if connected:
                print(f"Already connected to {connected}.")
            else:
                print("No active connection. Scanning for available networks...")
                available = get_available_networks()
                stored = get_stored_networks()

                for ssid in available:
                    if ssid in stored:
                        print(f"Attempting to connect to {ssid}...")
                        connect_to_network(
                            ssid, password=stored[ssid], interface=interface
                        )
                        break
                else:
                    print("No preferred networks found.")
        except Exception as ex:
            print(f"An error occurred: {ex}")
            logging.exception("An error occurred in run_watcher")

        time.sleep(300)  # Wait for 5 minutes before checking again


def main():
    parser = argparse.ArgumentParser(description="WiFi Checker")
    parser.add_argument(
        "--scan", action="store_true", help="Scan for available networks"
    )
    parser.add_argument(
        "--connected", action="store_true", help="Show connected wifi network"
    )
    parser.add_argument(
        "--wifi", action="store_true", help="List available Wi-Fi interfaces"
    )
    parser.add_argument("--stored", action="store_true", help="Show stored networks")
    parser.add_argument(
        "--connect", metavar="SSID", help="Connect to a specified network"
    )
    parser.add_argument(
        "--password", metavar="PASSWORD", help="Password for the specified network"
    )
    parser.add_argument(
        "--interface",
        metavar="INTERFACE",
        default=INTERFACE,
        help="Network interface to use",
    )

    args = parser.parse_args()

    if args.scan:
        available = get_available_networks()
        print("Available networks:")
        for ssid in available:
            print(ssid)
    elif args.connected:
        connected = get_connected_network()
        if connected:
            print(f"Connected to {connected}.")
        else:
            print("Not connected to any network.")
    elif args.wifi:
        interfaces = get_wifi_interfaces()
        print("Wi-Fi interfaces:")
        for interface in interfaces:
            print(interface)
    elif args.stored:
        stored = get_stored_networks()
        print("Stored networks:")
        for ssid, password in stored.items():
            print(f"{ssid}: {password}")
    elif args.connect and args.password:
        connect_to_network(args.connect, args.password, args.interface)
    else:
        print("Starting watcher...")
        run_watcher(args.interface)


if __name__ == "__main__":
    main()
