#!/usr/bin/env python3
import json
import logging
import os
import sys
import threading

from flask import Flask, request
from gevent.pywsgi import WSGIServer
import requests

from stratum import settings
from stratum.stratum_server import StratumServer

settings.DEBUG = False

class EthereumRPC:
    def __init__(self, host, port, path, ssl=False):
        self.host = host
        self.port = port
        self.path = path
        self.ssl = ssl

    def _url(self):
        protocol = 'https' if self.ssl else 'http'
        return f"{protocol}://{self.host}:{self.port}{self.path}"

    def eth_get_work(self):
        data = {"jsonrpc": "2.0", "id": 0, "method": "eth_getWork", "params": []}
        return self._post(data)

    def eth_submit_work(self, worker, nonce, header_hash, mix_digest):
        params = [nonce, header_hash, mix_digest]
        data = {"jsonrpc": "2.0", "id": 0, "method": "eth_submitWork", "params": params}
        return self._post(data)

    def _post(self, data):
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self._url(), json=data, headers=headers)
            return response.json()
        except Exception as e:
            logging.error(f"Ethereum RPC Error: {e}")
            return None

class EthereumStratumProxy:
    def __init__(self, ethereum_rpc):
        self.ethereum_rpc = ethereum_rpc
        self.stratum_server = StratumServer(self)

    def start(self, host, port):
        logging.info(f"Starting Ethereum Stratum Proxy on {host}:{port}")
        self.stratum_server.start(host, port)

    def get_work(self):
        work = self.ethereum_rpc.eth_get_work()
        if work and "result" in work:
            return work["result"]
        return None

    def submit_work(self, worker, nonce, header_hash, mix_digest):
        return self.ethereum_rpc.eth_submit_work(worker, nonce, header_hash, mix_digest)

app = Flask(__name__)

proxy = None

@app.route('/', methods=['POST'])
def handle_rpc():
    req = request.get_json()
    if not req:
        return {"error": "Invalid JSON request"}, 400

    method = req.get("method")
    params = req.get("params", [])

    if method == "eth_getWork":
        result = proxy.get_work()
        if result:
            return {"jsonrpc": "2.0", "id": req.get("id", 0), "result": result}
        else:
            return {"error": "Unable to get work"}, 500

    elif method == "eth_submitWork":
        if len(params) != 3:
            return {"error": "Invalid params"}, 400
        result = proxy.submit_work(None, params[0], params[1], params[2])
        if result:
            return {"jsonrpc": "2.0", "id": req.get("id", 0), "result": result.get("result", False)}
        else:
            return {"error": "Unable to submit work"}, 500

    return {"error": "Unsupported method"}, 400


def main():
    global proxy

    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"Config file {config_path} not found!")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = json.load(f)

    eth_rpc_config = config["ethereumstratumproxy"]["ethereumrpc"]
    ethereum_rpc = EthereumRPC(
        host=eth_rpc_config["host"],
        port=eth_rpc_config["port"],
        path=eth_rpc_config["path"],
        ssl=eth_rpc_config["ssl"]
    )

    proxy = EthereumStratumProxy(ethereum_rpc)

    stratum_host = config["ethereumstratumproxy"]["host"]
    stratum_port = config["ethereumstratumproxy"]["port"]

    threading.Thread(target=lambda: proxy.start(stratum_host, stratum_port), daemon=True).start()

    wsgi = WSGIServer(('0.0.0.0', 8555), app)
    wsgi.serve_forever()

if __name__ == "__main__":
    main()
