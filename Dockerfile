FROM python:2.7-alpine

ENV SCHEDULE **None**
ENV GOCRON_VERSION=${GOCRON_VERSION:-v0.0.7}

ADD https://github.com/odise/go-cron/releases/download/$GOCRON_VERSION/go-cron-linux.gz /usr/local/bin/go-cron
RUN chmod u+x /usr/local/bin/go-cron
ADD https://raw.githubusercontent.com/andrey-pohilko/registry-cli/master/requirements-build.txt /
COPY requirements.txt /
RUN pip install -r /requirements.txt
ADD https://raw.githubusercontent.com/andrey-pohilko/registry-cli/master/registry.py /
RUN sed -i -E 's|try_oauth = requests\.post\(request_url, auth=auth, \*\*kwargs\)|try_oauth = requests\.get\(request_url, auth=auth, \*\*kwargs\)|g' /registry.py
COPY *.py /
COPY *.sh /


CMD ["sh", "run.sh"]
