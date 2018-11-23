from datetime import datetime, timedelta, timezone


def timestamp_secs_to_datetime(ts: int) -> datetime:
    """
    Converts an integer timestamp (milliseconds since the Epoch) to timezone-aware datetime object
    :param ts: timestamp
    :return:
    """
    return datetime.fromtimestamp(ts, timezone.utc)


def timestamp_millis_to_datetime(ts: float) -> datetime:
    """
    Converts an integer timestamp (milliseconds since the Epoch) to timezone-aware datetime object
    :param ts: timestamp
    :return:
    """
    return datetime.fromtimestamp(ts / 1000.0, timezone.utc)

def datetime_to_timestamp(t: datetime) -> int:
    """
    Converts a datetime to an integer timestamp (seconds since the Epoch)
    :param t:
    :return:
    """
    return int(t.timestamp())


def datetime_to_str(t: datetime) -> str:
    """
    Converts a datetime to an string representation with integer seconds
    such as 2018-11-23T02:52:57Z

    :param t:
    :return:
    """
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def datetime_to_str_millis(t: datetime) -> str:
    """
    Converts a datetime to a string representation with fractional seconds such as
    2018-11-23T02:52:57.345000Z
    :param t:
    :return:
    """
    return t.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def str_to_datetime(s: str) -> datetime:
    """
    Parses a datetime string to a datetime object
    :param s:
    :return:
    """
    if '.' in s:
        dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    dt.replace(tzinfo=timezone.utc)
    return dt
