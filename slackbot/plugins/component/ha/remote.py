# -*- coding: utf-8 -*-

"""
Support for an interface to work with a remote instance of Home Assistant.

If a connection error occurs while communicating with the API a
HomeAssistantError will be raised.

For more details about the Python API, please refer to the documentation at
https://home-assistant.io/developers/python_api/
"""
from datetime import datetime
import datetime as dt
import enum
import json
import logging as _LOGGER
import urllib2, urllib, urlparse
import re
from types import DictProxyType
import requests
import pytz
import dateutil.parser as DateParser

#_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_HA_AUTH = 'X-HA-access'
SERVER_PORT = 8123
URL_API = '/api/'
URL_API_EVENTS = '/api/events'
URL_API_EVENTS_EVENT = '/api/events/{}'
URL_API_SERVICES = '/api/services'
URL_API_CONFIG = '/api/config'
URL_API_SERVICES_SERVICE = '/api/services/{}/{}'
URL_API_STATES = '/api/states'
URL_API_STATES_ENTITY = '/api/states/{}'
HTTP_HEADER_CONTENT_TYPE = 'Content-type'
CONTENT_TYPE_JSON = 'application/json'

ENTITY_ID_PATTERN = re.compile(r"^(\w+)\.(\w+)$")

UTC = DEFAULT_TIME_ZONE = pytz.utc
CST = pytz.timezone('Asia/Shanghai')

def valid_entity_id(entity_id):
    """Test if an entity ID is a valid format."""
    return ENTITY_ID_PATTERN.match(entity_id) is not None

def as_local(dattim):
    """Convert a UTC datetime object to local time zone."""
    if dattim.tzinfo == DEFAULT_TIME_ZONE:
        return dattim
    elif dattim.tzinfo is None:
        dattim = UTC.localize(dattim)
        return dattim
    else:
        dattim = dattim.astimezone(CST)
    return dattim

def utcnow():
    """Get now in UTC time."""
    return datetime.now(UTC)

DATETIME_RE = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$'
)

def parse_datetime(dt_str):
    """Parse a string and return a datetime.datetime.
    This function supports time zone offsets. When the input contains one,
    the output uses a timezone with a fixed offset from UTC.
    Raises ValueError if the input is well formatted but not a valid datetime.
    Returns None if the input isn't well formatted.
    """
    match = DATETIME_RE.match(dt_str)
    if not match:
        return None
    kws = match.groupdict()  # type: Dict[str, Any]
    if kws['microsecond']:
        kws['microsecond'] = kws['microsecond'].ljust(6, '0')
    tzinfo_str = kws.pop('tzinfo')

    tzinfo = None  # type: Optional[dt.tzinfo]
    if tzinfo_str == 'Z':
        tzinfo = UTC
    elif tzinfo_str is not None:
        offset_mins = int(tzinfo_str[-2:]) if len(tzinfo_str) > 3 else 0
        offset_hours = int(tzinfo_str[1:3])
        offset = dt.timedelta(hours=offset_hours, minutes=offset_mins)
        if tzinfo_str[0] == '-':
            offset = -offset
        tzinfo = pytz.timezone(offset)
    else:
        tzinfo = None
    kws = {k: int(v) for k, v in kws.items() if v is not None}
    kws['tzinfo'] = tzinfo
    return datetime(**kws)

def repr_helper(inp):
    """Help creating a more readable string representation of objects."""
    if isinstance(inp, (dict, DictProxyType)):
        return ", ".join(
                repr_helper(key)+"="+repr_helper(item) for key, item
                in inp.items())
    elif isinstance(inp, datetime):
        return as_local(inp.encode('utf-8')).isoformat()

    elif isinstance(inp, unicode):
        return '{}'.format(inp.encode('utf-8'))

    return '{}'.format(inp)

class HomeAssistantError(Exception):
    """General Home Assistant exception occurred."""

    pass

class State(object):
    """Object to represent a state within the state machine.
    entity_id: the entity that is represented.
    state: the state of the entity
    attributes: extra information on entity and state
    last_changed: last time the state was changed, not the attributes.
    last_updated: last time this object was updated.
    """

    __slots__ = ['entity_id', 'state', 'attributes',
                 'last_changed', 'last_updated']

    def __init__(self, entity_id, state, attributes=None, last_changed=None,
                 last_updated=None):
        """Initialize a new state."""
        if not valid_entity_id(entity_id):
            raise InvalidEntityFormatError((
                "Invalid entity id encountered: {}. "
                "Format should be <domain>.<object_id>").format(entity_id))

        self.entity_id = entity_id.lower()
        self.state = str(state)
        self.attributes = dict(attributes or {})
        self.last_updated = last_updated or utcnow()
        self.last_changed = last_changed or self.last_updated

    @property
    def domain(self):
        """Domain of this state."""
        return split_entity_id(self.entity_id)[0]

    @property
    def object_id(self):
        """Object id of this state."""
        return split_entity_id(self.entity_id)[1]

    @property
    def name(self):
        """Name of this state."""
        return (
            self.attributes.get(ATTR_FRIENDLY_NAME) or
            self.object_id.replace('_', ' '))

    def as_dict(self):
        """Return a dict representation of the State.
        Async friendly.
        To be used for JSON serialization.
        Ensures: state == State.from_dict(state.as_dict())
        """
        return {'entity_id': self.entity_id,
                'state': self.state,
                'attributes': dict(self.attributes),
                'last_changed': self.last_changed,
                'last_updated': self.last_updated}

    @classmethod
    def from_dict(cls, json_dict):
        """Initialize a state from a dict.
        Async friendly.
        Ensures: state == State.from_json_dict(state.to_json_dict())
        """
        if not (json_dict and 'entity_id' in json_dict and
                'state' in json_dict):
            return None

        last_changed = json_dict.get('last_changed')

        if isinstance(last_changed, (unicode, str)):
            #last_changed = parse_datetime(last_changed)
            last_changed = DateParser.parse(last_changed)

        last_updated = json_dict.get('last_updated')

        if isinstance(last_updated, (unicode, str)):
            #last_updated = parse_datetime(last_updated)
            last_updated = DateParser.parse(last_updated)

        return cls(json_dict['entity_id'], json_dict['state'],
                   json_dict.get('attributes'), last_changed, last_updated)

    def __eq__(self, other):
        """Return the comparison of the state."""
        return (self.__class__ == other.__class__ and
                self.entity_id == other.entity_id and
                self.state == other.state and
                self.attributes == other.attributes)

    def __repr__(self):
        """Return the representation of the states."""
        attr = "; {}".format(repr_helper(self.attributes)) \
               if self.attributes else ""

        return "<state {}={}{} @ {}>".format(
            self.entity_id, self.state, attr,
            as_local(self.last_changed).isoformat())

METHOD_GET = 'get'
METHOD_POST = 'post'
METHOD_DELETE = 'delete'


class APIStatus(enum.Enum):
    """Representation of an API status."""

    # pylint: disable=no-init, invalid-name
    OK = "ok"
    INVALID_PASSWORD = "invalid_password"
    CANNOT_CONNECT = "cannot_connect"
    UNKNOWN = "unknown"

    def __str__(self):
        """Return the state."""
        return self.value


class API(object):
    """Object to pass around Home Assistant API location and credentials."""

    def __init__(self, host, api_password=None,
                 port=SERVER_PORT, use_ssl=False):
        """Init the API."""
        self.host = host
        self.port = port
        self.api_password = api_password

        if host.startswith(("http://", "https://")):
            self.base_url = host
        elif use_ssl:
            self.base_url = "https://{}".format(host)
        else:
            self.base_url = "http://{}".format(host)

        if port is not None:
            self.base_url += ':{}'.format(port)

        self.status = None
        self._headers = {
            HTTP_HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON,
        }

        if api_password is not None:
            self._headers[HTTP_HEADER_HA_AUTH] = api_password

    def validate_api(self, force_validate=False):
        """Test if we can communicate with the API."""
        if self.status is None or force_validate:
            self.status = validate_api(self)

        return self.status == APIStatus.OK

    def __call__(self, method, path, data=None, timeout=5):
        """Make a call to the Home Assistant API."""
        if data is not None:
            data = json.dumps(data, cls=JSONEncoder)

        url = urlparse.urljoin(self.base_url, path)

        try:
            if method == METHOD_GET:
                return requests.get(
                    url, params=data, timeout=timeout, headers=self._headers)

            return requests.request(
                method, url, data=data, timeout=timeout,
                headers=self._headers)

        except requests.exceptions.ConnectionError:
            _LOGGER.exception("Error connecting to server")
            raise HomeAssistantError("Error connecting to server")

        except requests.exceptions.Timeout:
            error = "Timeout when talking to {}".format(self.host)
            _LOGGER.exception(error)
            raise HomeAssistantError(error)

    def __repr__(self):
        """Return the representation of the API."""
        return "<API({}, password: {})>".format(
            self.base_url, 'yes' if self.api_password is not None else 'no')


class JSONEncoder(json.JSONEncoder):
    """JSONEncoder that supports Home Assistant objects."""

    # pylint: disable=method-hidden
    def default(self, o):
        """Convert Home Assistant objects.

        Hand other objects to the original method.
        """
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, set):
            return list(o)
        elif hasattr(o, 'as_dict'):
            return o.as_dict()

        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            # If the JSON serializer couldn't serialize it
            # it might be a generator, convert it to a list
            try:
                return [self.default(child_obj)
                        for child_obj in o]
            except TypeError:
                # Ok, we're lost, cause the original error
                return json.JSONEncoder.default(self, o)


def validate_api(api):
    """Make a call to validate API."""
    try:
        req = api(METHOD_GET, URL_API)

        if req.status_code == 200:
            return APIStatus.OK

        elif req.status_code == 401:
            return APIStatus.INVALID_PASSWORD

        return APIStatus.UNKNOWN

    except HomeAssistantError:
        return APIStatus.CANNOT_CONNECT


def get_event_listeners(api):
    """List of events that is being listened for."""
    try:
        req = api(METHOD_GET, URL_API_EVENTS)

        return req.json() if req.status_code == 200 else {}

    except (HomeAssistantError, ValueError):
        # ValueError if req.json() can't parse the json
        _LOGGER.exception("Unexpected result retrieving event listeners")

        return {}


def fire_event(api, event_type, data=None):
    """Fire an event at remote API."""
    try:
        req = api(METHOD_POST, URL_API_EVENTS_EVENT.format(event_type), data)

        if req.status_code != 200:
            _LOGGER.error("Error firing event: %d - %s",
                          req.status_code, req.text)

    except HomeAssistantError:
        _LOGGER.exception("Error firing event")


def get_state(api, entity_id):
    """Query given API for state of entity_id."""
    try:
        req = api(METHOD_GET, URL_API_STATES_ENTITY.format(entity_id))

        # req.status_code == 422 if entity does not exist

        return State.from_dict(req.json()) \
            if req.status_code == 200 else None

    except (HomeAssistantError, ValueError):
        # ValueError if req.json() can't parse the json
        _LOGGER.exception("Error fetching state")

        return None


def get_states(api):
    """Query given API for all states."""
    try:
        req = api(METHOD_GET,
                  URL_API_STATES)

        return [State.from_dict(item) for
                item in req.json()]

    except (HomeAssistantError, ValueError, AttributeError):
        # ValueError if req.json() can't parse the json
        _LOGGER.exception("Error fetching states")

        return []


def remove_state(api, entity_id):
    """Call API to remove state for entity_id.

    Return True if entity is gone (removed/never existed).
    """
    try:
        req = api(METHOD_DELETE, URL_API_STATES_ENTITY.format(entity_id))

        if req.status_code in (200, 404):
            return True

        _LOGGER.error("Error removing state: %d - %s",
                      req.status_code, req.text)
        return False
    except HomeAssistantError:
        _LOGGER.exception("Error removing state")

        return False


def set_state(api, entity_id, new_state, attributes=None, force_update=False):
    """Tell API to update state for entity_id.

    Return True if success.
    """
    attributes = attributes or {}

    data = {'state': new_state,
            'attributes': attributes,
            'force_update': force_update}

    try:
        req = api(METHOD_POST,
                  URL_API_STATES_ENTITY.format(entity_id),
                  data)

        if req.status_code not in (200, 201):
            _LOGGER.error("Error changing state: %d - %s",
                          req.status_code, req.text)
            return False

        return True

    except HomeAssistantError:
        _LOGGER.exception("Error setting state")

        return False


def is_state(api, entity_id, state):
    """Query API to see if entity_id is specified state."""
    cur_state = get_state(api, entity_id)

    return cur_state and cur_state.state == state


def get_services(api):
    """Return a list of dicts.

    Each dict has a string "domain" and a list of strings "services".
    """
    try:
        req = api(METHOD_GET, URL_API_SERVICES)

        return req.json() if req.status_code == 200 else {}

    except (HomeAssistantError, ValueError):
        # ValueError if req.json() can't parse the json
        _LOGGER.exception("Got unexpected services result")

        return {}


def call_service(api, domain, service, service_data=None, timeout=5):
    """Call a service at the remote API."""
    try:
        req = api(METHOD_POST,
                  URL_API_SERVICES_SERVICE.format(domain, service),
                  service_data, timeout=timeout)

        if req.status_code != 200:
            _LOGGER.error("Error calling service: %d - %s",
                          req.status_code, req.text)

    except HomeAssistantError:
        _LOGGER.exception("Error calling service")


def get_config(api):
    """Return configuration."""
    try:
        req = api(METHOD_GET, URL_API_CONFIG)

        if req.status_code != 200:
            return {}

        result = req.json()
        if 'components' in result:
            result['components'] = set(result['components'])
        return result

    except (HomeAssistantError, ValueError):
        # ValueError if req.json() can't parse the JSON
        _LOGGER.exception("Got unexpected configuration results")

        return {}
