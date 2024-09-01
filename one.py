import json
import time
import requests
from typing import List, Dict

API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b"
HEADERS = {"Authorization": "Bearer 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"}

def read_prompts(filename: str) -> List[str]:
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def call_gemma_api(prompt: str) -> str:
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    generated_text = response.json()[0]['generated_text']
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):].strip()
    return generated_text

def process_prompts(prompts: List[str]) -> List[Dict]:
    results = []
    for prompt in prompts:
        time_sent = int(time.time())
        try:
            response = call_gemma_api(prompt)
        except Exception as e:
            response = f"Error occurred: {str(e)}"
        time_received = int(time.time())
        
        results.append({
            "Prompt": prompt,
            "Message": response,
            "TimeSent": time_sent,
            "TimeRecvd": time_received,
            "Source": "Gemma-2b"
        })
    
    return results

def write_output(data: List[Dict], filename: str):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)

def main():
    input_file = "input.txt"
    output_file = "output.json"
    
    prompts = read_prompts(input_file)
    results = process_prompts(prompts)
    write_output(results, output_file)
    
    print(f"Processing complete. Results written to {output_file}")

if __name__ == "__main__":
    main()