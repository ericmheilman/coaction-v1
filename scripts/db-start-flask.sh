#!/bin/sh

rm /home/ec2-user/leaderboard/server/leaderboard.db && sudo systemctl restart flask_app.service && sudo systemctl status flask_app.service
