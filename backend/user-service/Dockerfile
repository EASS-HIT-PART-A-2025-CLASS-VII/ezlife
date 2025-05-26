# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the shared db.py and models.py from the build context (now ./backend)
COPY db.py /app/db.py
COPY models.py /app/models.py

# Copy the user-service specific files into the container at /app
COPY user-service/main.py /app/main.py
COPY user-service/requirements.txt /app/requirements.txt

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
