# Docker Control Center

Docker Control Center is a lightweight Django web application allowing the user to control **docker-compose projects** as well as regular **standalone docker containers**.

It has built-in permissions to control who can view and execute different commands like start/stop/remove on projects or services.

#### Quick Start

Pull the image:
```
docker pull nanofab/control_center
```

Create a configuration folder where static files, settings, db and logs will be created.<br>
For example `/opt/control_center_config`, or `C:\control_center_config` and use the path in the commands below.


If you have a docker-compose file, simply run:
```
docker run --detach --publish 8000:8000 --volume /var/run/docker.sock:/var/run/docker.sock --volume <path to your docker-compose.yml parent folder>:/control-center/compose/:ro --volume <path to your control center configuration folder>/:/control-center/config/ nanofab/control_center
```

If you don't have a docker-compose file, run:
```
docker run --detach --publish 8000:8000 --volume /var/run/docker.sock:/var/run/docker.sock --volume <path to your control center configuration folder>/:/control-center/config/ nanofab/control_center
```

Then run (to create the first admin user):

```
docker run --interactive --tty --volume <path to control center configuration folder>/:/control-center/config/ nanofab/control_center django-admin createsuperuser
```

access the application at http://localhost:8000/ and log in using the previously created credentials

# Settings
Docker compose control center can be customized by adding parameters to the `settings.py` file inside your control-center configuration directory.

#### Windows Host
If your host is a windows machine, add:
```python
WINDOWS_HOST = True
```

#### Allowed Host
If you are using anything else than localhost to access the application, add:
```python
ALLOWED_HOSTS = ["<ip>", "<hostname>", ...]
```

#### Private Registry
If you are using a private docker registry, add:
```python
PRIVATE_DOCKER_REPOSITORY = {
    "available": True,
    "username": "user",
    "password": "pass",
    "url": "registry.gitlab.com",
}
``` 

#### Compose Project
If you are using a custom project name (different from the default parent directory name), add:
```python
COMPOSE_PROJECT = "<your-project-name>"
```

#### Compatibility Mode
If you want to use docker-compose in compatibility mode, add:
```python
COMPATIBILITY_MODE = True
```

From docker-compose documentation:
```
--compatibility     If set, Compose will attempt to convert deploy
                    keys in v3 files to their non-Swarm equivalent
```

#### Auto Refresh
Pages can be set to auto refresh (if you are showing container statuses on an always-on display).<br>
Simply add the number of seconds between refresh:
```python
AUTO_REFRESH = "30"
```


#### Site Title
Some titles can be customized by adding:
```python
SITE_TITLE = "My Title"
LOGIN_TITLE = "My Login Page Title"
```

#### Custom Service URL & Logos
When using a docker-compose file, you can customize each service's logo and URL by providing a `docker-compose.ini` config file next to your docker-compose.yml.<br>
Here is an example of what it would look like (paths are relative to the config file location):

```ini
[nginx]
logo = media/nginx.png

[control-center]
logo = media/control-center.png
url = http://www.mysite.com/controlcenter
```

#### Database connection
If you want to change the default SQLite Database, refer to the [documentation on django's website](https://docs.djangoproject.com/en/2.1/ref/databases/).

## Authentication

#### Username & password
The default authentication is done using username/password but its use is discouraged in production environments


#### LDAP
You can authenticate via LDAP by setting the following:
```python
AUTHENTICATION_BACKENDS = ["control_center.libs.authentication.backends.LDAPAuthenticationBackend"]

LDAP_SERVERS = [{
    "url": "your.ldap.url",
    "domain": "YOUR_DOMAIN", 
    "certificate": "<path to optional certificate>"
    }]
```

#### HTTP header
This is not recommended for production environment unless behind a proxy like Nginx which would set the specific header

```python
# The key part here is "control_center.libs.authentication.middleware.HTTPHeaderAuthenticationMiddleware"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "control_center.libs.authentication.middleware.HTTPHeaderAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = ["control_center.libs.authentication.backends.RemoteUserAuthenticationBackend"]

# optional, defaults to Authorization
# AUTHENTICATION_HEADER = "remote_user"
```


#### Kerberos
Another option is to use [Nginx with kerberos module](https://hub.docker.com/r/nanofab/nginx) to authenticate and then set the following:
```python
# The key part here is "control_center.libs.authentication.middleware.HTTPHeaderAuthenticationMiddleware"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "control_center.libs.authentication.middleware.HTTPHeaderAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = ['control_center.libs.authentication.backends.NginxKerberosAuthorizationHeaderAuthenticationBackend']
```

### Advanced Configuration

You can find all the application settings and their default values here: [Default Settings](https://github.com/usnistgov/docker-control-center/blob/master/control_center/base_settings.py)

Any of those can be overridden in your settings.py file