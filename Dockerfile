FROM alpine:3.7

ENV SCHEDULE **None**
ENV GOCRON_VERSION=${GOCRON_VERSION:-v0.0.6}

RUN apk update && \
    apk add python2 py2-pip curl && \
    curl -L --insecure https://github.com/odise/go-cron/releases/download/$GOCRON_VERSION/go-cron-linux.gz | zcat > /usr/local/bin/go-cron && \
    chmod u+x /usr/local/bin/go-cron && \
    apk del curl

ADD https://raw.githubusercontent.com/andrey-pohilko/registry-cli/master/registry.py /
ADD https://raw.githubusercontent.com/andrey-pohilko/registry-cli/master/requirements-build.txt /
COPY requirements.txt *.py *.sh /

RUN pip install -r /requirements.txt && \
    apk del py2-pip && \
    rm -rf /var/cache/apk/* && \
    sed -i -E 's|try_oauth = requests\.post\(request_url, auth=auth, \*\*kwargs\)|try_oauth = requests\.get\(request_url, auth=auth, \*\*kwargs\)|g' /registry.py

CMD ["sh", "run.sh"]
