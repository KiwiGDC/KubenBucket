# Étape 1 : build du CSS avec Node.js
FROM node:18-alpine AS build-css

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY tailwind.config.js ./
COPY assets ./assets

RUN npm run build:css

# Étape 2 : image finale Python slim
FROM python:3.11-slim

# Installer clamav et dépendances
RUN apt-get update && apt-get install -y \
    clamav \
    clamav-daemon \
    && rm -rf /var/lib/apt/lists/*

RUN freshclam || true

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Copier uniquement le CSS buildé depuis l'étape build-css
COPY --from=build-css /app/static/css/styles.css /app/static/styles.css

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
