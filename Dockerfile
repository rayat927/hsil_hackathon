FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \  # English language pack
    libgl1-mesa-glx \    # For OpenCV/Pillow if used
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest
COPY . .

ENV PYTHONUNBUFFERED=TRUE
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000", "--timeout", "120"]