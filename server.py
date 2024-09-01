import socket
import threading
import json
import requests
import time
import sys

API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b"
HEADERS = {"Authorization": "Bearer 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"}

class LLMServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()
        self.processed_prompts = 0
        self.total_prompts = 0
        self.server_socket = None

    def start(self):
        for attempt in range(10):  # Try 10 different ports
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen()
                print(f"Server listening on {self.host}:{self.port}")
                break
            except OSError:
                print(f"Port {self.port} is in use, trying next one.")
                self.port += 1
                if attempt == 9:
                    print("Failed to find an open port. Exiting.")
                    sys.exit(1)

        while True:
            client, address = self.server_socket.accept()
            print(f"New connection from {address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client,))
            client_thread.start()

    def handle_client(self, client):
        with self.lock:
            self.clients.append(client)
    
        buffer = ""
        while True:
            try:
                data = client.recv(1024).decode('utf-8')
                if not data:
                    break
                buffer += data
                while True:
                    try:
                        # Try to parse the JSON object from the buffer
                        prompt, index = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[index:].strip()  # Remove the parsed JSON object from the buffer
                    except json.JSONDecodeError:
                        # If JSON is not complete, break and wait for more data
                        break
    
                    with self.lock:
                        self.total_prompts += 1
                    response = self.call_llm_api(prompt['prompt'])
                    self.send_message(client, json.dumps({
                        'client_id': prompt['client_id'],
                        'prompt': prompt['prompt'],
                        'response': response
                    }))
                    with self.lock:
                        self.processed_prompts += 1
                        print(f"Processed {self.processed_prompts}/{self.total_prompts} prompts")
                        if self.processed_prompts == self.total_prompts:
                            self.close_all_connections()
            except json.JSONDecodeError:
                print(f"Received invalid JSON: {buffer}")
                buffer = ""  # Clear the buffer if invalid JSON is detected

    def call_llm_api(self, prompt):
        try:
            payload = {"inputs": prompt}
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            full_response = response.json()[0]['generated_text']
            return full_response.replace(prompt, "").strip()
        except requests.RequestException as e:
            print(f"API call failed: {e}")
            return f"Error: Unable to get response from API. {str(e)}"

    def send_message(self, client, message):
        try:
            message = message.encode('utf-8')
            message_length = len(message).to_bytes(4, byteorder='big')
            client.sendall(message_length + message)
        except Exception as e:
            print(f"Error sending message: {e}")

    def close_all_connections(self):
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        if self.server_socket:
            self.server_socket.close()
        print("Server shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    server = LLMServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server interrupted. Shutting down.")
        server.close_all_connections()