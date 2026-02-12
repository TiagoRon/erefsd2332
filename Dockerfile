# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (FFmpeg, ImageMagick, Fonts)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow text
# (MoviePy needs this to write text)
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create output directories
RUN mkdir -p output

# Make sure the font exists or use a default
# (You might need to copy your specific font in the COPY step)

# Run cloud_main.py when the container launches
CMD ["python", "cloud_main.py"]
