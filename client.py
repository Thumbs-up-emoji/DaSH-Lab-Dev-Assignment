import socket
import json
import time
import sys
import threading

class LLMClient:
    def __init__(self, host='localhost', port=5000, client_id=None, input_file=None, output_file=None):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.input_file = input_file
        self.output_file = output_file
        self.socket = None
        self.results = []
        self.expected_responses = 0
        self.received_responses = 0
        self.lock = threading.Lock()

    def connect(self):
        for attempt in range(5):  # Try to connect 5 times
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                print(f"Connected to server {self.host}:{self.port}")
                return True
            except socket.error as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(2)  # Wait for 2 seconds before retrying
        print("Failed to connect to the server after multiple attempts.")
        return False

    def send_prompts(self):
        with open(self.input_file, 'r') as file:
            prompts = [line.strip() for line in file if line.strip()]

        self.expected_responses = len(prompts)
        for prompt in prompts:
            message = json.dumps({
                'client_id': self.client_id,
                'prompt': prompt
            })
            self.socket.sendall(message.encode('utf-8'))
            print(f"Sent prompt: {prompt}")

    def receive_responses(self):
        while self.received_responses < self.expected_responses:
            try:
                message_length = int.from_bytes(self.socket.recv(4), byteorder='big')
                data = self.receive_all(message_length)
                if not data:
                    break
                response = json.loads(data)
                time_received = int(time.time())
                result = {
                    "ClientID": self.client_id,
                    "Prompt": response['prompt'],
                    "Message": response['response'],
                    "TimeSent": int(time.time()),  # Approximation
                    "TimeRecvd": time_received,
                    "Source": "Gemma-2b" if response['client_id'] == self.client_id else "user"
                }
                with self.lock:
                    self.results.append(result)
                    self.received_responses += 1
                print(f"Received response {self.received_responses}/{self.expected_responses} for prompt: {response['prompt'][:30]}...")
            except Exception as e:
                print(f"Error receiving response: {e}")
                break

    def receive_all(self, n):
        data = bytearray()
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data.decode('utf-8')

    def write_results(self):
        with open(self.output_file, 'w') as file:
            json.dump(self.results, file, indent=2)
        print(f"Results written to {self.output_file}")

    def run(self):
        try:
            if not self.connect():
                return
            self.send_prompts()
            self.receive_responses()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if self.socket:
                self.socket.close()
            self.write_results()  # Ensure results are written even if an error occurs

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 client.py <client_id> <input_file> <output_file> <server_port>")
        sys.exit(1)

    client_id, input_file, output_file, port = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    client = LLMClient(client_id=client_id, input_file=input_file, output_file=output_file, port=port)
    client.run()