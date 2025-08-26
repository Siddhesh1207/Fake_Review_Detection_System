# Use an official Python image that includes common build tools
FROM python:3.9-slim-bookworm

# Install the Fortran compiler using Debian's package manager
RUN apt-get update && apt-get install -y gfortran

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your Flask app runs on
EXPOSE 5000

# Define the command to run your application
CMD ["gunicorn", "system:app"]
