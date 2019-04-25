from _ssl import PROTOCOL_TLSv1_2, CERT_REQUIRED
from base64 import b64decode
from logging import exception, getLogger

from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend, ModelBackend
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from ldap3 import Tls, Server, Connection, AUTO_BIND_TLS_BEFORE_BIND, SIMPLE
from ldap3.core.exceptions import LDAPBindError, LDAPExceptionError

logger = getLogger(__name__)

system_name = settings.LOGIN_TITLE if settings.LOGIN_TITLE else "System"


class RemoteUserAuthenticationBackend(RemoteUserBackend):
    """ The web server performs Kerberos authentication and passes the user name in via the REMOTE_USER environment variable. """

    create_unknown_user = False

    def clean_username(self, username):
        """
		User names arrive in the form user@DOMAIN.NAME.
		This function chops off Kerberos realm information (i.e. the '@' and everything after).
		"""
        return username.partition("@")[0]


class NginxKerberosAuthorizationHeaderAuthenticationBackend(ModelBackend):
    """ The web server performs Kerberos authentication and passes the user name in via the HTTP_AUTHORIZATION header. """

    def authenticate(self, request, username=None, password=None, **keyword_arguments):
        # Perform any custom security checks below.
        # Returning None blocks the user's access.
        username = self.clean_username(request.META.get("HTTP_AUTHORIZATION", None))

        # The user must exist in the database
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(
                f"Username {username} attempted to authenticate with Kerberos via Nginx, but that username does not exist in the {system_name} database. The user was denied access."
            )
            return None

        # The user must be marked active.
        if not user.is_active:
            logger.warning(
                f"User {username} successfully authenticated with Kerberos via Nginx, but that user is marked inactive in the {system_name} database. The user was denied access."
            )
            return None

        # All security checks passed so let the user in.
        logger.debug(
            f"User {username} successfully authenticated with Kerberos via Nginx and was granted access to {system_name}."
        )
        return user

    def clean_username(self, username):
        """
		User names arrive encoded in base 64, similar to Basic authentication, but with a bogus password set (since .
		This function chops off Kerberos realm information (i.e. the '@' and everything after).
		"""
        if not username:
            return None
        pieces = username.split()
        if len(pieces) != 2:
            return None
        if pieces[0] != "Basic":
            return None
        return b64decode(pieces[1]).decode().partition(":")[0]


class LDAPAuthenticationBackend(ModelBackend):
    """ This class provides LDAP authentication against an LDAP or Active Directory server. """

    @method_decorator(sensitive_post_parameters("password"))
    def authenticate(self, request, username=None, password=None, **keyword_arguments):
        if not username or not password:
            return None

        # The user must exist in the database
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(
                f"Username {username} attempted to authenticate with LDAP, but that username does not exist in the {system_name} database. The user was denied access."
            )
            return None

        # The user must be marked active.
        if not user.is_active:
            logger.warning(
                f"User {username} successfully authenticated with LDAP, but that user is marked inactive in the {system_name} database. The user was denied access."
            )
            return None

        for server in settings.LDAP_SERVERS:
            try:
                t = Tls(validate=CERT_REQUIRED, version=PROTOCOL_TLSv1_2, ca_certs_file=server["certificate"])
                s = Server(server["url"], port=636, use_ssl=True, tls=t)
                c = Connection(
                    s,
                    user="{}\\{}".format(server["domain"], username),
                    password=password,
                    auto_bind=AUTO_BIND_TLS_BEFORE_BIND,
                    authentication=SIMPLE,
                )
                c.unbind()
                # At this point the user successfully authenticated to at least one LDAP server.
                return user
            except LDAPBindError as e:
                logger.warning(
                    f"User {username} attempted to authenticate with LDAP, but entered an incorrect password. The user was denied access."
                )
                # When this error is caught it means the username and password were invalid against the LDAP server.
            except LDAPExceptionError as e:
                exception(e)

        # The user did not successfully authenticate to any of the LDAP servers.
        return None
