# 使用python3.12.1-slim镜像(slim镜像比alpine镜像更小,更安全)
FROM python:3.12.1-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 设置工作目录
WORKDIR /app

# 复制requirements.txt文件到容器(利用dockerfile的上下文缓存机制,避免每次构建都重新安装依赖)
COPY requirements.txt /app/

# 安装依赖,使用清华源,提高安装速度
RUN pip install --progress-bar off -U pip -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60
RUN pip install --progress-bar off -U setuptools -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60
RUN pip install --progress-bar off -U wheel -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60
RUN pip install --progress-bar off --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 180

# 复制应用代码到容器
COPY . /app

# 暴露应用端口
EXPOSE 80

# 设置应用环境变量
ENV APP_ENV "prod"

# 运行应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips", "*"]
