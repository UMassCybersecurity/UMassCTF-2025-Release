FROM python:latest 

# Install Python
# RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*
RUN pip install pycryptodome

# Set working directory
WORKDIR /app

# Copy ynetd and the Python script into the container
COPY ynetd chall.py flag.txt ./

# Make ynetd and the script executable
RUN chmod +x ynetd chall.py

# Expose the port that ynetd will listen on
EXPOSE 40444

# Start ynetd to serve the Python script
CMD ["./ynetd", "-p", "40444", "python chall.py"]