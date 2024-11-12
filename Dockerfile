FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .

# Install MariaDB Connector/C and build tools
RUN apt-get update && apt-get install -y \
    mariadb-client \
    libmariadb-dev-compat \
    libmariadb-dev \
    build-essential

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]