import logging
import socket
import threading

def setup(socket, proxy):
    return StratumHandler(socket, proxy)

class StratumHandler(threading.Thread):
    def __init__(self, sock, proxy):
        threading.Thread.__init__(self)
        self.sock = sock
        self.proxy = proxy
        self.running = True
        self.start()

    def run(self):
        try:
            self.sock.settimeout(10)
            while self.running:
                data = self.sock.recv(4096)
                if not data:
                    break
                message = data.decode().strip()
                if message:
                    response = self.handle_message(message)
                    if response:
                        self.sock.sendall((response + '\n').encode())
        except socket.timeout:
            logging.warning("Socket timeout")
        except Exception as e:
            logging.error(f"StratumHandler error: {e}")
        finally:
            self.sock.close()

    def handle_message(self, message):
        logging.info(f"Received message: {message}")
        try:
            params = message.split()
            if params[0] == "mining.subscribe":
                return "subscribed"
            elif params[0] == "mining.authorize":
                return "authorized"
            elif params[0] == "mining.submit":
                if len(params) < 4:
                    return "error: invalid submit params"
                nonce, header_hash, mix_digest = params[1:4]
                result = self.proxy.submit_work(None, nonce, header_hash, mix_digest)
                return "accepted" if result and result.get("result") else "rejected"
            else:
                return "error: unsupported method"
        except Exception as e:
            logging.error(f"handle_message error: {e}")
            return "error: internal server error"
