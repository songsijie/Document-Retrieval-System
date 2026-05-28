import os

APP_NAME = os.getenv("APP_NAME", "Document Retrieval System")
IS_DEBUG = os.getenv("IS_DEBUG", "false").lower() == "true"

SVR_HOST = os.getenv("SVR_HOST", "0.0.0.0")
SVR_PORT = int(os.getenv("SVR_PORT", "8000"))
SVR_TIMEOUT = int(os.getenv("SVR_TIMEOUT", "10"))
MIDDLEWARE_EXCLUDE_PATHS = ["/docs", "/redoc", "/openapi.json", "/health"]
RATE_LIMIT_EXCLUDE_PATHS = ["/docs", "/redoc", "/openapi.json", "/health"]
ALLOWED_IPS = [ip.strip() for ip in os.getenv("ALLOWED_IPS", "127.0.0.1").split(",") if ip.strip()]

CACHE_HOST = os.getenv("CACHE_HOST", "127.0.0.1")
CACHE_PORT = int(os.getenv("CACHE_PORT", "6379"))
CACHE_PASSWORD = os.getenv("CACHE_PASSWORD") or None
CACHE_DB = int(os.getenv("CACHE_DB", "0"))
CACHE_KEYPREFIX = os.getenv("CACHE_KEYPREFIX", "document_retrieval")

ES_HOSTS = os.getenv("ES_HOSTS", "")
ES_USERNAME = os.getenv("ES_USERNAME") or None
ES_PASSWORD = os.getenv("ES_PASSWORD") or None
ES_API_KEY = os.getenv("ES_API_KEY") or None
ES_INDEX = os.getenv("ES_INDEX", "articles")
ES_REQUEST_TIMEOUT = int(os.getenv("ES_REQUEST_TIMEOUT", "30"))
