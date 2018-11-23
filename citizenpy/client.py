from datetime import datetime, timedelta
from citizenpy.timestamp import datetime_to_str_millis
from typing import List

import requests

from citizenpy.models import IncidentId, IncidentV1, UserInfo

from citizenpy.token_util import parse_jwt_token, create_guest_token

API_SERVICE_URL = 'https://api.sp0n.io'
DATA_SERVICE_URL = 'https://data.sp0n.io'
INCIDENT_SERVICE_URL = 'https://i.citizen.com'

DEFAULT_USER_AGENT = 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'


class CitizenBaseException(Exception):
    pass


class CitizenAuthException(CitizenBaseException):
    pass


class Client(object):
    """
    Main client class
    """
    def __init__(self, user_agent=DEFAULT_USER_AGENT):
        self.user_agent = user_agent

    def guest_session(self):
        token = create_guest_token()
        requestor = Requestor(token=token, user_agent=self.user_agent)
        return GuestSession(requestor)

    def auth_session(self, username, password):
        pass


class Requestor(object):
    """
    API session that manages tokens
    """
    def __init__(self, token, user_agent=DEFAULT_USER_AGENT):
        """
        Creates a session object with a given token
        :param token: sessio token
        :param user_agent: User Agent string to use when making requests
        """
        self.token = token
        self.parsed_token = parse_jwt_token(self.token)
        self.user_agent = user_agent

    def set_token(self, token: str):
        """
        Sets session token
        :param token:
        :return:
        """
        self.token = token
        self.parsed_token = parse_jwt_token(self.token)

    def get_token(self) -> str:
        """
        :return: Session token string
        """
        return self.token

    def get_expires(self) -> datetime:
        """
        :return: datetime object describing when the session token is scheduled to expire
        """
        return self.parsed_token.expires

    def get_created_at(self) -> datetime:
        """
        :return: datetime object describing when the session token was issued
        """
        return self.parsed_token.created_at

    def get_user_id(self) -> str:
        """
        :return: User ID associated with the session or None if it's a guest session
        """
        return self.parsed_token.user_id

    def expires_soon(self) -> bool:
        """
        Check if the session token is about to expire and must be renewed
        :return: True if the token has expired or is going to expire within a minute
        """
        if self.parsed_token is None:
            return False
        return datetime.now() + timedelta(minutes=1) > self.get_expires()

    def set_user_agent(self, user_agent: str):
        """
        Sets the user-agent header
        :param user_agent:
        :return:
        """
        self.user_agent = user_agent

    def _get_headers(self):
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json'
        }
        # this may be overridden by retry logic
        token = self.get_token()
        if token is not None:
            headers['x-access-token'] = token
        return headers

    def get(self, host: str, path: str, params: dict=None) -> dict:
        """
        Makes a GET API request
        :param host: API server to send data to
        :param path: endpoint path
        :param params: parameters as a dict
        :return:
        """
        result = requests.get(host + path, params=params, headers=self._get_headers())
        if result.status_code == requests.codes.ok:
            return result.json()  # TODO: catch errors
        self.raise_for_status(result)

    def post(self, host: str, path: str, params: dict) -> dict:
        """
        Makes a POST API request
        :param host: API server to send data to
        :param path: endpoint path
        :param params: parameters as a dict
        :return:
        """
        print (params)
        result = requests.post(host + path, json=params, headers=self._get_headers())
        if result.status_code == requests.codes.ok:
            return result.json()  # TODO: catch errors
        # result_json = result.json()
        # raise CitizenException(result.status_code, result_json['error'])
        result.raise_for_status()

    @staticmethod
    def raise_for_status(result: requests.Response):
        if result.status_code == 400:
            error_json = result.json()
            error = error_json.get('error', result.reason)
            raise CitizenAuthException(error)
        result.raise_for_status()


class GuestSession(object):
    """
    This class contains API calls that do not require an authenticated session
    """
    def __init__(self, requestor: Requestor):
        self.requestor = requestor

    def get_user_id(self) -> str:
        return self.requestor.get_user_id()

    def get_token(self) -> str:
        return self.requestor.get_token()

    def get_nearby_incident_ids(
            self,
            min_lat: float,
            max_lat: float,
            min_long: float,
            max_long: float,
            limit: int=100) -> List[IncidentId]:
        # Ensure bounds are correctly ordered
        if max_lat < min_lat:
            min_lat, max_lat = max_lat, min_lat
        if max_long < min_long:
            min_long, max_long = max_long, min_long
        result = self.requestor.get(DATA_SERVICE_URL, '/v1/incidents/nearby', {
            'upperLatitude': max_lat,
            'lowerLatitude': min_lat,
            'upperLongitude': max_long,
            'lowerLongitude': min_long,
            'limit': limit
        })
        return result['results']

    def get_incidents_v1(self, incident_ids: List[str], page_size: int=100) -> List[IncidentV1]:
        if len(incident_ids) == 0:
            return []

        all_incidents = []
        for i in range(0, len(incident_ids), page_size):
            page_ids = incident_ids[i:i+page_size]
            result = self.requestor.get(DATA_SERVICE_URL, '/gnet/incidents1/batch', {
                'incidentIds': ','.join(page_ids)
            })
            incidents = result.get('incidents', [])
            all_incidents += incidents

        return [IncidentV1(incident) for incident in all_incidents]

    def query(self,
              since: datetime,
              min_lat: float,
              max_lat: float,
              min_long: float,
              max_long: float,
              service_areas: List[str]=None) -> List[IncidentId]:
        if service_areas is None:
            service_areas = []
        # Ensure bounds are correctly ordered
        if max_lat < min_lat:
            min_lat, max_lat = max_lat, min_lat
        if max_long < min_long:
            min_long, max_long = max_long, min_long

        result = self.requestor.post(DATA_SERVICE_URL, '/gnet/incidents1/query', {
            'since': datetime_to_str_millis(since),
            'bounds': {
                'upperLatitude': max_lat,
                'lowerLatitude': min_lat,
                'upperLongitude': max_long,
                'lowerLongitude': min_long
            },
            'serviceAreas': service_areas
        })
        return result['incidentIds']

    def queryV2(self,
              since: datetime,
              min_lat: float,
              max_lat: float,
              min_long: float,
              max_long: float,
              service_areas: List[str]=None) -> List[IncidentId]:
        if service_areas is None:
            service_areas = []
        # Ensure bounds are correctly ordered
        if max_lat < min_lat:
            min_lat, max_lat = max_lat, min_lat
        if max_long < min_long:
            min_long, max_long = max_long, min_long

        result = self.requestor.post(DATA_SERVICE_URL, '/incidents2/query', {
            'since': datetime_to_str_millis(since),
            'bounds': {
                'upperLatitude': max_lat,
                'lowerLatitude': min_lat,
                'upperLongitude': max_long,
                'lowerLongitude': min_long
            },
            'serviceAreas': service_areas
        })
        return result['incidentIds']

    def get_leaders(self):
        result = self.requestor.get(DATA_SERVICE_URL, '/radio/leaders')
        return result['leaders']

    def get_clips(self, channels):
        result = self.requestor.post(DATA_SERVICE_URL, '/radio/clips', {
            'channels': channels
        })
        # Server can return {'clips': null} so we have to handle this case and always return an iterable
        return result.get('clips') or []

    def get_sub_areas(self):
        result = self.requestor.get(DATA_SERVICE_URL, '/radio/sub_areas')
        return result.get('SubAreas') or []

    def get_channels(self):
        result = self.requestor.get(DATA_SERVICE_URL, '/v2/radio/channels')
        return result.get('channels') or []

    def get_suggested_radius(self, latitude, longitude):
        result = self.requestor.get(DATA_SERVICE_URL, '/signal/suggested_radius', {
            'lat': latitude, 'long': longitude
        })
        return result

    def get_service_area_code(self, latitude, longitude):
        result = self.requestor.get(DATA_SERVICE_URL, '/signal/service_area_code', {
            'lat': latitude, 'long': longitude
        })
        return result

    def get_neighborhoods(self, latitude, longitude):
        result = self.requestor.get(DATA_SERVICE_URL, '/geo/neighborhoods', {
            'lat': latitude, 'long': longitude
        })
        return result.get('results') or []

    def get_precincts(self, latitude, longitude):
        result = self.requestor.get(DATA_SERVICE_URL, '/geo/precincts', {
            'lat': latitude, 'long': longitude
        })
        return result.get('results') or []

    def authenticate(self, username, password):
        result = self.requestor.post(API_SERVICE_URL, "/api/authenticate", {
            "identifier": username,
            "password": password
        })
        auth_token = result['userToken']
        auth_requestor = Requestor(auth_token, user_agent=self.requestor.user_agent)
        return AuthSession(auth_requestor)


class AuthSession(GuestSession):
    """
    This class contains API calls that require an authenticated session
    """
    def __init__(self, requestor):
        super().__init__(requestor)

    def get_user(self, user_id=None):
        if user_id is None:
            user_id = self.get_user_id()
        result = self.requestor.get(API_SERVICE_URL, '/api/user/{}'.format(user_id))
        return UserInfo(result)
