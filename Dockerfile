FROM admintuts/python:3.9.7-buster-slim
USER root
RUN set -ex \
    && mkdir -p /usr/src/app \
    && chown 1001:1001 -R /usr/src/app \
    && chmod 700 -R /usr/src/app

USER python

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

VOLUME [ "/usr/src/app" ]

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]