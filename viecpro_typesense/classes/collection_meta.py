from . import O
from .parsers import CollectionParser
from .configs import configs



class CollectionMeta(type):

    """
    """

    def __new__(cls, name, bases, attrs):
        """
    
        """

        cfg = None if not "Config" in attrs.keys() else attrs.pop("Config")

        cls_inst = super().__new__(cls, name, bases, attrs)
        cls_inst.parser = CollectionParser(owner=cls_inst)

        cls_inst.config = cls_inst.parser.parse_config(
            cfg
        )  

   

        cls_inst.fields = []

        from .fields import FieldMeta, StaticField, Field

        for k, v in attrs.items():
            if not k.startswith("__"):
                if isinstance(v, StaticField):
                    cls_inst.fields.append(v)

                elif isinstance(v, (FieldMeta, Field)):
                    setattr(v.config, "model", cfg.model)
                    v._deferred_init()
                    cls_inst.fields.append(v)

        return cls_inst

    def __repr__(self):
        return f"<{self.__name__}>"
