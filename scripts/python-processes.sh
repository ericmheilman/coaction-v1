#!/bin/sh
# Get the Process IDs (PIDs) of all running Python3 processes
python3_pids=$(pgrep -f "python3")

# Print Python3 processes with their PIDs and ports
for pid in $python3_pids; do
    process_cmd=$(ps -p $pid -o cmd=)
    process_ports=$(sudo netstat -tulnep 2>/dev/null | grep "$pid/python3" | awk '{print $4}')
    echo "PID: $pid | Command: $process_cmd | Ports: $process_ports"
done

