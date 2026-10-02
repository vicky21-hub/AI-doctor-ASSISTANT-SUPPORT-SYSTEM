# ==============================================================================
# Stage 1: Build Frontend (Vite + React)
# ==============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy frontend source files
COPY index.html vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json tailwind.config.js postcss.config.js ./
COPY public ./public
COPY src ./src

# Set empty API base so client makes same-origin requests in production
ENV VITE_API_BASE=""
RUN npm run build

# ==============================================================================
# Stage 2: Production Python Backend + Static Hosting
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend ./backend

# Copy built frontend assets into Flask's static distribution folder
COPY --from=frontend-builder /app/dist ./backend/static_dist

# Ensure database and uploads folders exist
RUN mkdir -p ./backend/database ./backend/uploads

WORKDIR /app/backend

# Production environment variables
ENV FLASK_ENV=production
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Run with Gunicorn production WSGI server
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 app:app"]

