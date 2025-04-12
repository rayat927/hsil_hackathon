# FROM python:3.9-slim

# # Install system dependencies
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     tesseract-ocr \
#     tesseract-ocr-eng \
#     libgl1-mesa-glx && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# # Copy requirements first for caching
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the rest
# COPY . .

# ENV PYTHONUNBUFFERED=TRUE
# ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000", "--timeout", "120"]

FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Flask/Werkzeug first to prevent conflicts
RUN pip install --no-cache-dir flask==2.0.3 werkzeug==2.0.3

# Then install other requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=TRUE
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000", "--timeout", "120"]