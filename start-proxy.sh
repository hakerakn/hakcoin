#!/bin/bash
cd $(dirname "$0")
python3 eth-proxy.py >> logs/proxy.log 2>&1 &
