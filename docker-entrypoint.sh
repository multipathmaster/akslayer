#!/bin/bash
az login --use-device-code
echo -e "Serving up on http://localhost:5000"
python3 akslayer_upgrader.py
