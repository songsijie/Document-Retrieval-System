import os

# 应用名称
APP_NAME = os.getenv("APP_NAME", "Document Retrieval System")
IS_DEBUG = os.getenv("IS_DEBUG", "true").lower() == "true"

# 服务主机
SVR_HOST = os.getenv("SVR_HOST", "127.0.0.1")
# 服务端口
SVR_PORT = int(os.getenv("SVR_PORT", "8000"))
# 服务超时时间
SVR_TIMEOUT = int(os.getenv("SVR_TIMEOUT", "10"))
# 中间件排除路径
MIDDLEWARE_EXCLUDE_PATHS = ["/docs", "/redoc", "/openapi.json", "/health"]
# 限流排除路径
RATE_LIMIT_EXCLUDE_PATHS = ["/docs", "/redoc", "/openapi.json", "/health"]
# 允许的IP地址
ALLOWED_IPS = [ip.strip() for ip in os.getenv("ALLOWED_IPS", "*").split(",") if ip.strip()]

# Redis 相关配置
CACHE_HOST = os.getenv("CACHE_HOST", "127.0.0.1")
CACHE_PORT = int(os.getenv("CACHE_PORT", "6379"))
CACHE_PASSWORD = os.getenv("CACHE_PASSWORD") or None
CACHE_DB = int(os.getenv("CACHE_DB", "0"))
CACHE_KEYPREFIX = os.getenv("CACHE_KEYPREFIX", "document_retrieval")

# Elasticsearch 相关配置
ES_HOSTS = os.getenv("ES_HOSTS", "http://localhost:9200")
ES_USERNAME = os.getenv("ES_USERNAME") or None
ES_PASSWORD = os.getenv("ES_PASSWORD") or None
ES_API_KEY = os.getenv("ES_API_KEY") or None
ES_INDEX = os.getenv("ES_INDEX", "articles")
ES_REQUEST_TIMEOUT = int(os.getenv("ES_REQUEST_TIMEOUT", "30"))
