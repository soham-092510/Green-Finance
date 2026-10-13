# Use official Python base image (lightweight version)
# WHY:
# - python:3.11-slim is smaller than full image → faster builds
# - Contains only essential tools needed to run Python
FROM python:3.11-slim


# Set working directory inside container
# WHY:
# - All commands will run from /app
# - Keeps project structure clean inside container
WORKDIR /app


# Copy requirements file into container
# WHY:
# - Done separately to leverage Docker caching
# - If requirements.txt doesn't change, dependencies won't reinstall
COPY requirements.txt .


# Install Python dependencies
# WHY:
# - Installs all packages needed for your backend (FastAPI, SQLAlchemy, etc.)
# - --no-cache-dir reduces image size (no pip cache stored)
RUN pip install --no-cache-dir -r requirements.txt


# Copy backend and frontend source code into container
COPY backend/ ./backend/
COPY frontend/ ./frontend/


# Expose port 8000
# WHY:
# - Documents that container listens on port 8000
# - Required for communication with host/docker-compose
EXPOSE 8000


# Command to run the application
# WHY:
# - Starts FastAPI app using Uvicorn server
# - backend.main:app → points to FastAPI instance
# - 0.0.0.0 → allows external access (important for Docker)
# - --port 8000 → runs on port 8000
# - --reload → auto-restart on code changes (development only)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]