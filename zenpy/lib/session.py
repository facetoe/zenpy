import requests


class SessionWrapper(object):
    session = None

    def __init__(self, email, password, token, session=None):
        self.email = email
        self.password = password
        self.token = token
        self._init_session(session if session else requests.Session())

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.session.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.session.delete(*args, **kwargs)

    def _init_session(self, session):
        headers = {'Content-type': 'application/json',
                   'User-Agent': 'Zenpy/0.0.22'}
        self.session = session
        self.session.auth = self._get_auth()
        self.session.headers.update(headers)
        return session

    def _get_auth(self):
        if self.password:
            return self.email, self.password
        else:
            return self.email + '/token', self.token