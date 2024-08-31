import socket
import json
import threading
import requests
from datetime import datetime
import sys
import time

API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b"
headers = {"Authorization": "Bearer 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"} 

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

class GemmaServer:
    def __init__(self, host='localhost', start_port=5000):
        self.host = host
        self.port = self.find_available_port(start_port)
        self.server_socket = None
        self.clients = []

    def find_available_port(self, start_port):
        for port in range(start_port, start_port + 1000):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except socket.error:
                continue
        raise RuntimeError("Could not find an available port")

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Server listening on {self.host}:{self.port}")
        except socket.error as e:
            print(f"Error starting server: {e}")
            sys.exit(1)

        with open('server_port.txt', 'w') as f:
            f.write(str(self.port))

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"New connection from {addr}")
            self.clients.append(client_socket)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        try:
            # Handshake
            client_socket.send("READY".encode('utf-8'))
            handshake = client_socket.recv(1024).decode('utf-8')
            if handshake != "READY":
                print(f"Handshake failed: {handshake}")
                return

            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                print(f"Received data: {data}")
                try:
                    prompt = json.loads(data)['prompt']
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

                time_sent = datetime.now().isoformat()

                payload = {
                    "inputs": prompt,
                    "parameters": {"max_length": 100}
                }

                try:
                    response = query(payload)
                    time_recvd = datetime.now().isoformat()

                    result = {
                        "Prompt": prompt,
                        "Message": response[0]["generated_text"] if response else "Error: No response",
                        "TimeSent": time_sent,
                        "TimeRecvd": time_recvd,
                        "Source": "Gemma API"
                    }

                    print(f"Sending response: {result}")
                    client_socket.send(json.dumps(result).encode('utf-8'))
                except Exception as e:
                    print(f"Error querying API: {e}")
                    error_response = {
                        "error": "Failed to query API",
                        "details": str(e)
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.clients.remove(client_socket)
            client_socket.close()

    def stop(self):
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients:
            client.close()

if __name__ == "__main__":
    server = GemmaServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server stopping...")
    finally:
        server.stop()