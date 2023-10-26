FROM python:3.8

RUN apt-get update && apt-get upgrade -y
RUN dpkg --purge remove docker docker-engine docker.io containerd runc
RUN curl -fsSL https://get.docker.com -o get-docker.sh
RUN sh get-docker.sh

RUN rm -f /etc/localtime \
	&& ln -s /usr/share/zoneinfo/America/New_York /etc/localtime

RUN pip install --upgrade pip

COPY . /control-center/
RUN pip install --no-cache-dir /control-center/ gunicorn==19.9.0
RUN rm --recursive --force /control-center/

RUN mkdir --parents /control-center/config control-center/compose
WORKDIR /control-center/config
COPY control_center/base_settings.py /control-center/base_settings.py
ENV DJANGO_SETTINGS_MODULE "base_settings"
ENV PYTHONPATH "/control-center/"

COPY gunicorn_configuration.py /etc/

EXPOSE 8000/tcp

VOLUME /control-center/compose
VOLUME /control-center/config

COPY start_in_docker.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start_in_docker.sh
CMD ["start_in_docker.sh"]