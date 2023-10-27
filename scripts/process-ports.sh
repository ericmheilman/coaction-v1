#!/bin/sh
sudo netstat -tuln | grep -E "(^Proto|LISTEN)" ; ps aux | awk '{print $2, $11}'

