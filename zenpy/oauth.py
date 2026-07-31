import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth, ClientSecretPost


class ClientCredentialsSession(requests.Session):
    """
    Session that manages OAuth 2.0 Client Credentials Grant tokens automatically:
    fetched lazily on first request and renewed proactively before expiry.
    """

    # Signals _init_session to skip the standard credential check
    authorized = True

    def __init__(self, subdomain, client_id, client_secret, scope, expires_in=None, domain="zendesk.com"):
        super().__init__()
        self.mount("https://", HTTPAdapter(max_retries=Retry(
            total=3,
            status_forcelist=[r for r in Retry.RETRY_AFTER_STATUS_CODES if r != 429],
            respect_retry_after_header=False,
        )))
        token_endpoint = "https://{}.{}/oauth/tokens".format(subdomain, domain)
        oauth2_client = OAuth2Client(
            token_endpoint=token_endpoint,
            auth=ClientSecretPost(client_id, client_secret),
            session=self,
        )
        token_kwargs = dict(scope=scope)
        if expires_in is not None:
            token_kwargs["expires_in"] = expires_in
        self.auth = OAuth2ClientCredentialsAuth(oauth2_client, **token_kwargs)
