#!/bin/bash

# Set the path to the lock file
LOCK_FILE="/tmp/my_flask_app.lock"

# Check if the lock file exists
if [ -f "$LOCK_FILE" ]; then
    echo "Another instance of the Flask app is already running. Exiting..."
    exit 1
fi

# Create the lock file
touch "$LOCK_FILE"

# Restart the Flask app service
sudo systemctl restart flask_app.service

# Follow the service logs
sudo journalctl -fu flask_app.service

# Remove the lock file when the service logs follow command exits
rm "$LOCK_FILE"

