# Backend for "Inspection Report by FRNFEB"
# Bundles Python + LibreOffice (needed for formula recalculation + PDF
# export) into one image so Railway/Render can just build & run this.
#
# IMPORTANT: this must be a Debian/Ubuntu base where we apt-install
# python3 itself (not the separate python:3.x-slim image). LibreOffice's
# Python bridge module ("uno") is only installed into the *system*
# python3's site-packages by the python3-uno apt package -- a
# self-compiled interpreter from python:3.x-slim can't see it, which is
# what caused "ModuleNotFoundError: No module named 'uno'" the first
# time around. Using --system-site-packages for the venv below lets our
# app's dependencies (fastapi, etc.) install cleanly on top while still
# seeing the system uno module.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    python3 \
    python3-venv \
    python3-uno \
    fonts-dejavu \
    fonts-liberation \
    fonts-texgyre \
    fonts-crosextra-carlito \
    fonts-crosextra-caladea \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m venv --system-site-packages /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY template ./template
COPY static ./static

RUN mkdir -p /app/jobs

# Railway/Render inject $PORT at runtime; default to 8000 for local/docker run
ENV PORT=8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
