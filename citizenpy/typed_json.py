from datetime import datetime, timedelta
import logging
import typing


def _parse_array(t):
    def parser(values):
        assert isinstance(values, list)
        return [t(value) for value in values]
    return parser


def _parse_dict(key_type, value_type):
    def parser(value):
        return {
            key_type(k): value_type(v) for k,v in value.items()
        }
    return parser


def _convert_to_parser(t):
    if isinstance(t, list):
        return _parse_array(_convert_to_parser(t[0]))
    elif isinstance(t, dict):
        k, v = next(iter(t.items()))
        return _parse_dict(_convert_to_parser(k), _convert_to_parser(v))
    elif callable(t):
        return t
    else:
        raise TypeError(f'Cannot convert Json to {t}')


class JsonTypeMeta(type):
    def __new__(mcs, typename, bases, ns):
        ns['__schema__'] = {n: _convert_to_parser(value) for n, value in ns.items() if not n.startswith('_')}
        return super().__new__(mcs, typename, bases, ns)


class JsonType(metaclass=JsonTypeMeta):
    def __init__(self, json_data):
        for k in json_data:
            if k not in self.__class__.__schema__:
                logging.warning(f'Unknown member {self.__class__.__name__}[{k}] = { json_data[k] }')
        for k, v in self.__class__.__schema__.items():
            if k in json_data:
                setattr(self, k, v(json_data[k]))
            else:
                setattr(self, k, None)

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.__dict__)})'


def anything(x):
    """
    Dummy parser that accepts anything
    :param x:
    :return:
    """
    return x


