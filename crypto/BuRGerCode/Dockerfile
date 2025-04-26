FROM debian:bookworm-slim 

# Install Python
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy ynetd and the Python script into the container
COPY ynetd server.py ./

# Make ynetd and the script executable
RUN chmod +x ynetd server.py

# Expose the port that ynetd will listen on
EXPOSE 40444

# Start ynetd to serve the Python script
CMD ["./ynetd", "-p", "40444", "./server.py"]