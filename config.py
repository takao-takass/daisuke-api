import os

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.30:30003",
    "https://192.168.1.30:30003"
]

secret = {
    "organization": os.getenv('OPENAI_ORGANIZATION', "org-xxxxxx"),
    "project": os.getenv('OPENAI_PROJECT', "proj-xxxxxx"),
    "api_key": os.getenv('OPENAI_API_KEY', "sk-xxxxxx"),
    "db_user": os.getenv('DB_USER', "root"),
    "db_host": os.getenv('DB_HOST', "localhost"),
    "db_password": os.getenv('DB_PASSWORD', "password"),
    "db_port": os.getenv('DB_PORT', "3306"),
    "db_name": os.getenv('DB_NAME', "chat")
}

conn_params = {
    "user": secret['db_user'],
    "password": secret['db_password'],
    "host": secret['db_host'],
    "port": int(secret['db_port']),
    "database": secret['db_name']
}