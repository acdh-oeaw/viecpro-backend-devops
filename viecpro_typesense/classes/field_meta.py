from .configs import configs
from .config import CollectionConfig
from .parsers import FieldParser

class FieldMeta(type):
    # TODO: remove, I think this is not used and or does nothing.
    config_attrs = configs["field_config"]["attrs"]


    def __new__(cls, name, bases, attrs):

        cls_inst = super().__new__(cls, name, bases, attrs)
        cls_inst._parser = FieldParser()

        return cls_inst
    

    def __init__(cls, name, bases, attrs):
        #print(f"init: {name=}")

        if "Config" in attrs.keys():
            cfg = attrs.pop("Config")
        else: 
            cfg = None
        
        cls.config = cls._parser.parse_config(cfg)


        super().__init__(name, bases, attrs)



        