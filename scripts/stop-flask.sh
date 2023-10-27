#!/bin/sh

sudo systemctl stop flask_app.service && python3 kill-5000.py
