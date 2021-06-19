FROM python:3.9-alpine
COPY . /app
RUN mkdir /app/mnt && \
    sed -i "s/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g" /etc/apk/repositories && \
    apk add --update --no-cache build-base linux-headers pcre-dev && \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ uwsgi && \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r /app/requirements.txt
CMD ["uwsgi", "--chdir=/app", "--pyargv=--database=/app/mnt/data.db", "-MT", "--socket=/app/mnt/app.sock", "--manage-script-name", "--mount=/app=main:app"]