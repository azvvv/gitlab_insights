# Build frontend
FROM node:24.12.0 AS frontend-build

WORKDIR /frontend

COPY frontend/ ./

RUN npm install

RUN npm run build

# Build backend
FROM python:3.13.4

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Copy the source code into the container
COPY src/ ./

# Copy frontend build artifacts to static folder
COPY --from=frontend-build /frontend/dist ./static

# Copy .env if it exists
COPY .env* ./

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]