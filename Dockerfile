FROM python:3.9-alpine
COPY . /app
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories && \
    apk add --update --no-cache build-base linux-headers && \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ uwsgi && \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -r /app/requirements.txt
