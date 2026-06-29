# Use the official Microsoft Playwright image optimized for Linux environments
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set up the internal application workspace
WORKDIR /app

# Copy the requirements manifest file explicitly into the workspace root
COPY requirements.txt /app/requirements.txt

# Run the installation sequence safely as isolated steps
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining core code infrastructure files
COPY . /app

# Open up the necessary operational communication port
EXPOSE 8000

# Start up the production web server instance
CMD ["python", "app.py"]
