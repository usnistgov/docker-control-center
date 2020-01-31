FROM centos:centos8

RUN yum --assumeye install dnf-plugins-core
RUN dnf --assumeyes update
RUN dnf --assumeyes install epel-release

RUN dnf --assumeye config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
RUN dnf --assumeyes install vim python3-pip docker-ce --nobest

RUN rm -f /etc/localtime \
	&& ln -s /usr/share/zoneinfo/America/New_York /etc/localtime

RUN pip3 install --upgrade pip

COPY . /control-center/
RUN pip3 install --no-cache-dir /control-center/ gunicorn==19.9.0
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