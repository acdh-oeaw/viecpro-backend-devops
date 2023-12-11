from .configs import configs

class configMeta(type):

    def __new__(cls, name, bases, attrs):
        #print("created new config class object", type(cls), cls)
        #print("bases: ", bases)

        return super().__new__(cls, name, bases, attrs)

class Config(metaclass=configMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CollectionConfig(Config):


    pass

class FieldConfig(Config):


    pass