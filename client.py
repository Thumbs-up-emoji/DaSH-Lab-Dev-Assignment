import socket
import json
import sys
import os
import time

def read_prompts(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def save_to_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

def read_server_port():
    max_retries = 10
    retry_delay = 1
    for _ in range(max_retries):
        try:
            with open('server_port.txt', 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            time.sleep(retry_delay)
    raise RuntimeError("Could not read server port")

class GemmaClient:
    def __init__(self, host='localhost'):
        self.host = host
        self.port = read_server_port()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                self.socket.connect((self.host, self.port))
                print(f"Connected to server on port {self.port}")
                
                # Handshake
                handshake = self.socket.recv(1024).decode('utf-8')
                if handshake != "READY":
                    print(f"Unexpected handshake: {handshake}")
                    raise RuntimeError("Handshake failed")
                self.socket.send("READY".encode('utf-8'))
                
                return
            except socket.error as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        raise RuntimeError("Failed to connect to the server")

    def send_prompt(self, prompt):
        message = json.dumps({"prompt": prompt})
        print(f"Sending prompt: {message}")
        self.socket.send(message.encode('utf-8'))

    def receive_response(self):
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                response = self.socket.recv(4096).decode('utf-8')
                print(f"Received raw response: {response}")
                return json.loads(response)
            except json.JSONDecodeError as e:
                print(f"JSON decoding error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Failed to decode JSON after multiple attempts")
                    return {"error": "Failed to decode server response"}

    def close(self):
        self.socket.close()

def main(input_file, output_file):
    client = GemmaClient()
    client.connect()

    prompts = read_prompts(input_file)
    results = []

    for prompt in prompts:
        try:
            client.send_prompt(prompt)
            response = client.receive_response()
            results.append(response)
        except Exception as e:
            print(f"Error processing prompt '{prompt}': {e}")
            results.append({"error": str(e), "prompt": prompt})

    save_to_json(results, output_file)
    print(f"Results saved to {output_file}")

    client.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.")
        sys.exit(1)

    main(input_file, output_file)