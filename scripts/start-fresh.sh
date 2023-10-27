#!/bin/sh
#sudo bash -c '/home/ec2-user/leaderboard/server/venv/bin/activate'
sudo systemctl restart react_app.service
sudo systemctl restart flask_app.service
sudo journalctl -fu flask_app.service

