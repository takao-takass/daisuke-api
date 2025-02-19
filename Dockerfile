FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .

# Install MariaDB Connector/C and build tools
RUN apt-get update && apt-get install -y \
    mariadb-client \
    libmariadb-dev-compat \
    libmariadb-dev \
    build-essential \
    openssl

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p certs

RUN if [ ! -f certs/certificate.crt ]; then \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./certs/private.key \
    -out ./certs/certificate.crt \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Development/CN=localhost"; \
    fi

EXPOSE 8000 8443

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8443", "--ssl-keyfile", "./certs/private.key", "--ssl-certfile", "./certs/certificate.crt"]