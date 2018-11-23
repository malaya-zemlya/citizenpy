"""
Utilities for encoding and decoding Citizen session tokens.
"""
from collections import namedtuple
from datetime import datetime, timedelta

import jwt

# Not really a secret, the key is encoded into every client
CLIENT_SECRET = 'b384d0cf2e5d976b4e6eace837919ed3b80d2057'

ParsedToken = namedtuple('ParsedToken', ['user_id', 'expires', 'created_at'])


def parse_jwt_token(token):
    """
    Parse session JWT token
    :param token: token string
    :return: ParsedToken named tuple containing extracted data
    """
    claims = jwt.decode(token, verify=False)
    return ParsedToken(
        user_id=claims.get('uid'),
        expires=datetime.fromtimestamp(claims.get('exp', 0)),
        created_at=datetime.fromtimestamp(claims.get('iat', 0))
    )


def create_guest_token(duration=None):
    """
    Creates a Guest token with a given expiry time.
    As far as we can tell, nobody actually checks the guest token for validity, but we are going to play nice
    :param duration: for how long the token will stay valid
    :return: token string
    """
    created_at = datetime.now() - timedelta(minutes=1) # Add buffer for server clock drift
    if duration is None:
        duration = timedelta(hours=24)
    expires = created_at + duration
    return jwt.encode(
        {
            'iat': int(created_at.timestamp()),
            'exp': int(expires.timestamp())
        },
        CLIENT_SECRET,
        algorithm='HS256')
