FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy the requirements file and install dependencies with increased timeout
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=500 -r requirements.txt

# Copy the entire project into the container.
COPY . .

EXPOSE $PORT

# Command to run the FastAPI app using uvicorn.
CMD ["uvicorn", "app.routes:app", "--host", "0.0.0.0", "--port", "${PORT:-10000}"]
