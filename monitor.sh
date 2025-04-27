#!/bin/bash
PROXY_DIR="$HOME/hak-eth-stratum-proxy"
LOG_FILE="$PROXY_DIR/logs/monitor.log"
START_SCRIPT="$PROXY_DIR/start-proxy.sh"

while true
do
    if ! pgrep -f "python3 eth-proxy.py" > /dev/null
    then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Proxy not running. Restarting..." >> "$LOG_FILE"
        bash "$START_SCRIPT"
    fi
    sleep 10
done
