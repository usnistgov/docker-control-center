from setuptools import setup, find_packages

VERSION = "5.0.0"

setup(
    name="docker_compose_control_center",
    version=VERSION,
    python_requires=">=3.14",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/usnistgov/docker-control-center",
    license="Public domain",
    author="Center for Nanoscale Science and Technology",
    author_email="CNSTapplications@nist.gov",
    description="Docker Compose Control Center is a small utility web application. It allows for control of docker containers, and specifically services created with docker-compose",
    long_description="Find out more about Docker Compose Control Center on the Github project page https://github.com/usnistgov/docker-control-center",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.14",
    ],
    install_requires=[
        "docker==7.1.0",
        "django==6.0",
        "PyYAML==6.0.3",
        # "docker-compose==1.29.2",
        "whitenoise==6.11.0",
        "requests==2.32.5",
        "ldap3==2.9.1",
        "pytz==2025.2",
        "python-dateutil==2.8.2",
        "djangorestframework==3.16.1",
    ],
)
