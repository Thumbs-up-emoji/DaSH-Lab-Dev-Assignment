FROM python:3.12

WORKDIR /ass

# Install virtualenv
RUN pip install virtualenv

# Create a virtual environment
RUN python -m virtualenv venv

# Copy the application code
COPY . .

# Make the run.sh script executable
RUN chmod +x run.sh

# Expose the port the server will run on
EXPOSE 5000

# Command to run the script
CMD ["./run.sh"]