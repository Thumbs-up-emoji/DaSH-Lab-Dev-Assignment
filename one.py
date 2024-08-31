import requests
import json
from datetime import datetime
import time

API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b"
headers = {"Authorization": "Bearer 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"} 

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def read_prompts(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def save_to_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    input_file = "input.txt"
    output_file = "output.json"
    
    prompts = read_prompts(input_file)
    results = []

    for prompt in prompts:
        time_sent = datetime.now().isoformat()
        
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 100}
        }
        
        response = query(payload)
        
        time_recvd = datetime.now().isoformat()
        
        result = {
            "Prompt": prompt,
            "Message": response[0]["generated_text"] if response else "Error: No response",
            "TimeSent": time_sent,
            "TimeRecvd": time_recvd,
            "Source": "Gemma API"
        }
        
        results.append(result)
        
        # Add a small delay to avoid overwhelming the API
        time.sleep(1)

    save_to_json(results, output_file)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()