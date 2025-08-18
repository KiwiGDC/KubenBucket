FROM python:3.11-slim


# Installer clamav et les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    clamav \
    clamav-daemon \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour la base de virus ClamAV (optionnel au build)
RUN freshclam || true

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app


EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
