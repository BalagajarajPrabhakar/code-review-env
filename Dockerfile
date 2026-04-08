FROM python:3.11-slim

WORKDIR /app



COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install -e .



# Start server
CMD ["python", "-m", "server.app"]