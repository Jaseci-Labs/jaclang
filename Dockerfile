# Dockerfile

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn

# Copy the server script and startup script to the container
COPY module_server_v2.py /app/
COPY startup.sh /app/
RUN chmod +x /app/startup.sh

# Set the default command to run the startup script
CMD ["/app/startup.sh"]
