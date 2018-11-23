from citizenpy.typed_json import JsonType
from citizenpy.timestamp import timestamp_millis_to_datetime, str_to_datetime
from typing import NewType, List

JwtToken = NewType('JwtToken', str)

IncidentId = NewType('IncidentId', str)

IncidentUpdateId = NewType('IncidentUpdateId', str)


class Dispatcher(JsonType):
    id = str
    name = str


class IncidentUpdate(JsonType):
    ts = timestamp_millis_to_datetime
    text = str
    id = IncidentUpdateId
    uid = str
    hlsReady = bool
    hlsDone = bool
    hlsVodDone = bool
    videoStreamId = str
    dispatcher = Dispatcher


class IncidentV1(JsonType):
    id = IncidentId
    title = str
    cityCode = str
    level = int
    neighborhood = str
    address = str
    location = str
    longitude = float
    latitude = float
    createdAt = str_to_datetime
    updatedAt = str_to_datetime
    updates = {str: IncidentUpdate}
    notified = int
    notifRadiusM = int


class PublicUserInfo(JsonType):
    city = str
    mission = str

class UserInfo(JsonType):
    appVersion = str
    cs = timestamp_millis_to_datetime
    deviceToken = str
    deviceTokenTs = timestamp_millis_to_datetime
    deviceTokenType = str
    email = str
    osVersion = str
    phone = str
    private = bool
    public = PublicUserInfo
    username = str
    hasPassword = bool
