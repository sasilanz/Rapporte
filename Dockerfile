FROM python:3.11-slim

WORKDIR /app

# Installiere Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere App-Code
COPY app/ ./app/

# Erstelle Datenverzeichnis
RUN mkdir -p /app/data

# Exponiere Port
EXPOSE 8085

# Starte die App
CMD ["python", "-m", "flask", "--app", "app.main", "run", "--host=0.0.0.0", "--port=8085"]
