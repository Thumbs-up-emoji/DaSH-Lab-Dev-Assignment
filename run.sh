#!/bin/bash

# Function to clean up processes
cleanup() {
    echo "Cleaning up..."
    # Kill all background processes
    kill $(jobs -p) 2>/dev/null
    wait $(jobs -p) 2>/dev/null
    # Remove the temporary port file
    rm -f server_port.txt
    echo "Cleanup complete."
    exit
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT INT TERM

# Check if input files exist
if [ ! -f input1.txt ] || [ ! -f input2.txt ]; then
    echo "Error: input1.txt or input2.txt does not exist."
    exit 1
fi

# Start the server
python3 server.py &
SERVER_PID=$!

# Wait for the server to start and write its port
max_retries=10
retry_delay=1
for i in $(seq 1 $max_retries); do
    if [ -f server_port.txt ]; then
        break
    fi
    echo "Waiting for server to start (attempt $i/$max_retries)..."
    sleep $retry_delay
done

if [ ! -f server_port.txt ]; then
    echo "Failed to start server. Exiting."
    exit 1
fi

SERVER_PORT=$(cat server_port.txt)
echo "Server started on port $SERVER_PORT"

# Start two clients
python3 client.py input1.txt output1.json &
python3 client.py input2.txt output2.json &

# Wait for all background processes to finish
wait

echo "All processes completed."