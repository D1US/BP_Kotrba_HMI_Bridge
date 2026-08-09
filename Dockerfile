FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask pyads

COPY bridge.py .

EXPOSE 5000

CMD ["python", "bridge.py"]
