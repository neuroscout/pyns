import requests
import re
from functools import partialmethod

from . import API_BASE_URL, ROUTE_PATTERN
from . import models

class Neuroscout(object):
    def __init__(self, email=None, password=None, api_base_url=None):
        self._session = requests.Session()
        self._api_base_url = api_base_url or API_BASE_URL
        self._api_token = None

        if email is not None and password is not None:
            self._authorize(email, password)

        # Set up main routes
        self.analyses = models.Analyses(self)
        self.datasets = models.Datasets(self)
        self.tasks = models.Tasks(self)
        self.runs = models.Runs(self)
        self.predictors = models.Predictors(self)
        self.predictor_events = models.PredictorEvents(self)
        self.datasets = models.Datasets(self)
        self.user = models.User(self)

    def _get_headers(self):
        if self._api_token is not None:
           return {'Authorization': 'JWT %s' % self._api_token}
        else:
            return None

    def _build_path(self, route, **kwargs):
        def _replace_variables(pattern, variables):
            """ Replaces variables in pattern, returning an empty string
                if any fail to match """
            for name in re.findall('\{(.*?)\}', pattern):
                if name in variables and variables[name] is not None:
                    di = {name: str(variables[name])}
                    pattern = pattern.format(**di)
                else:
                    return ''

            return pattern

        new_path = ROUTE_PATTERN
        optional_patterns = re.findall('\[(.*?)\]', ROUTE_PATTERN)

        for pattern in optional_patterns:
            chunk = _replace_variables(pattern, kwargs)
            new_path = new_path.replace('[%s]' % pattern, chunk)

        return new_path.format(base_url=self._api_base_url, route=route)

    def _make_request(self, request, route, sub_route=None, id=None,
                      params=None, headers=None, **data):
        """ Generic request handler """
        request_function = getattr(self._session, request)
        headers = headers or self._get_headers()
        route = self._build_path(route, sub_route=sub_route, id=id)

        return request_function(
            route, json=data, headers=headers, params=params)

    def _authorize(self, email=None, password=None):
        rv = self._post('auth', data={'email': email, 'password': password})

        self._api_token = rv.json()['access_token']

    _get = partialmethod(_make_request, 'get')
    _post = partialmethod(_make_request, 'post')
    _put = partialmethod(_make_request, 'put')
    _delete = partialmethod(_make_request, 'delete')
