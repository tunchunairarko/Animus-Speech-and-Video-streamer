from collections import namedtuple
from typing import Any
import animus_utils as utils
import inflection

from google.protobuf.json_format import MessageToDict, ParseDict


def convert_animus_response_to_dict(animus_response):
    if not animus_response:
        return {
            "success": True,
            "description": '',
            "code": 1
            }
    
    return {
        "success": animus_response.success,
        "description": animus_response.description,
        "code": animus_response.code
    }

def dict_to_proto_obj(dictObj):
    return ParseDict(dictObj,utils.SetupRobotProto)

def proto_obj_to_dict(proto_object: Any) -> str:
    return MessageToDict(proto_object)

def proto_obj_list_to_dict(proto_object_list: Any) -> str:
    dict_list = []
    
    for proto_object in proto_object_list:
        dict_list.append(MessageToDict(proto_object))
    
    return dict_list

def dictToSnakeCaseObject(camelCasedDict):
    snakeCasedDict = dict()

    for key in camelCasedDict:
        snake_cased_property = inflection.underscore(key)
        snakeCasedDict[snake_cased_property] = camelCasedDict[key]
    
    return namedtuple('Robot', snakeCasedDict.keys())(*snakeCasedDict.values())