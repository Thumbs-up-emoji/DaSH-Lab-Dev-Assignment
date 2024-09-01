#!/bin/bash

# Function to kill background processes
cleanup() {
    echo "Cleaning up..."
    jobs -p | xargs -r kill
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT

# Start the server
python3 server.py &
SERVER_PID=$!

# Wait for the server to start
sleep 2

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Server failed to start. Exiting."
    exit 1
fi

# Start the clients
python3 client.py client1 input1.txt output1.json 5000 &
CLIENT1_PID=$!

python3 client.py client2 input2.txt output2.json 5000 &
CLIENT2_PID=$!

# Wait for all processes to finish
wait $CLIENT1_PID
wait $CLIENT2_PID

echo "All processes completed."