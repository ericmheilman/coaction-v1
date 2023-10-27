#!/bin/sh

sudo systemctl stop flask_app.service && sudo systemctl restart flask_app.service && sudo journalctl -fu flask_app.service
