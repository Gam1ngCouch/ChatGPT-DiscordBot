# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libsodium-dev \
    bash \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install virtualenv
RUN pip install virtualenv

# Create a virtual environment
RUN virtualenv /root/myenv

# Copy the current directory contents into the container at /app
COPY . /app

# Activate the virtual environment and install any needed packages specified in requirements.txt
RUN /bin/bash -c "source /root/myenv/bin/activate && pip install --no-cache-dir -r requirements.txt"

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the application with the virtual environment activated
CMD ["/bin/bash", "-c", "source /root/myenv/bin/activate && python discord_bot.py"]
