# camper_wifi
Automatically connect to a wifi network if available


copy `wifi_checker.service` to `/etc/systemd/system/wifi_checker.service`

Then execute the following commands to enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wifi_checker.service
sudo systemctl start wifi_checker.service
```

to check status use `sudo journalctl -u wifi_checker.service`
