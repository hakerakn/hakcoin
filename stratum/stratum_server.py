import logging
import socket
import threading
from stratum import server

class StratumServer(threading.Thread):
    def __init__(self, proxy):
        threading.Thread.__init__(self)
        self.proxy = proxy
        self.host = None
        self.port = None
        self.running = False
        self.sock = None

    def start(self, host, port):
        self.host = host
        self.port = port
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(100)
        logging.info(f"Stratum server started on {self.host}:{self.port}")

        try:
            while self.running:
                client_sock, addr = self.sock.accept()
                logging.info(f"Accepted connection from {addr}")
                server.setup(client_sock, self.proxy)
        except Exception as e:
            logging.error(f"Stratum server error: {e}")
        finally:
            self.sock.close()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
