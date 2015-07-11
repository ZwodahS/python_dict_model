#           DO WHAT THE F*** YOU WANT TO PUBLIC LICENSE
#                   Version 2, December 2004
#
# Copyright (C) 2015- ZwodahS(github.com/ZwodahS)
# zwodahs.github.io
#
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#           DO WHAT THE F*** YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#  0. You just DO WHAT THE F*** YOU WANT TO.
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

"""
mongo plugin, requires labels
"""

import arrow
import shortuuid
from ..dict_model import *
from .labels import LabelMixin

DATETIME_STORE_PRECISION_V1 = 1e6

class MongoMixin(Mixin):

    @classmethod
    def map_to_mongo(cls, document):
        if document is None:
            return
        for key, definition in cls._fields.items():
            value = document.get(key)
            if value is not None:
                if isinstance(definition, DefinedDictField) and issubclass(definition.model, MapToMongoMixin):
                    definition.model.map_to_mongo(value)
                elif isinstance(definition, ListField) and isinstance(definition.inner_type, DefinedDictField):
                    for v in value:
                        definition.inner_type.model.map_to_mongo(v)
                else:
                    if hasattr(definition, "reversed_choices") and definition.reversed_choices is not None:
                        if isinstance(definition, ListField):
                            document[key] = [ definition.choices.get(v) for v in value ]
                        else:
                            document[key] = definition.choices.get(value)
                    if isinstance(definition, DateTimeField):
                        document[key] = arrow.get(value).float_timestamp * DATETIME_STORE_PRECISION_V1 # store all datetime microseconds
                    if hasattr(definition, "store_field"):
                        document[definition.store_field] = document[key]
                        document.pop(key)

    @classmethod
    def map_from_mongo(cls, document):
        if document is None:
            return
        for key, definition in cls._fields.items():
            if hasattr(definition, "store_field") and definition.store_field in document:
                document[key] = document.pop(definition.store_field)
            value = document.get(key)
            if value is not None:
                if isinstance(definition, DefinedDictField) and issubclass(definition.model, MapToMongoMixin):
                    definition.model.map_from_mongo(value)
                elif isinstance(definition, ListField) and isinstance(definition.inner_type, DefinedDictField):
                    for v in value:
                        definition.inner_type.model.map_from_mongo(v)
                else:
                    if hasattr(definition, "reversed_choices") and definition.reversed_choices is not None:
                        if isinstance(definition, ListField):
                            document[key] = [ definition.reversed_choices.get(v) for v in value ]
                        else:
                            document[key] = definition.reversed_choices.get(value)
                    if isinstance(definition, DateTimeField):
                        document[key] = microsecond_to_datetime(document[key])



def microsecond_to_datetime(microsecond):
    """convert microsecond to datetime properly.
    datetime.datetime.fromtimestamp(1432550134353845/1e6)
    datetime.datetime(2015, 5, 25, 10, 35, 34, 353844)
    need to deal with cases like this
    """
    seconds_part = int(microsecond//1e6)
    microseconds_part = int(microsecond%1e6)
    return arrow.get(seconds_part).replace(microsecond=microseconds_part).datetime
