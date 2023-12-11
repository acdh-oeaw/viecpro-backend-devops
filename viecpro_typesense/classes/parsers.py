from viecpro_typesense.defaults import collection_prefix
from django.conf import settings
from . import O
from .configs import configs
from typing import Iterable
from django.db.models import Field as DJ_FIELD
from .config import FieldConfig, CollectionConfig


def parse_config(cfg, attrs, config_object):
    config = config_object()
    for k, v in attrs.items():
        setattr(config, k, v)

    if cfg:
        for k, v in cfg.__dict__.items():
            if not k.startswith("__"):
                if not k in attrs.keys():
                    raise Exception(
                        f"Configuration error {k} is not an allowed attribute. Allowed attributes are: {attrs.keys()}"
                    )
                else:
                    setattr(config, k, v)

    return config


if hasattr(settings, "DJANGO_TYPESENSE"):
    col_prefix = settings.DJANGO_TYPESENSE.get(
        "collection_prefix", collection_prefix)
else:
    col_prefix = collection_prefix


class FieldParser:
    def __init__(self, owner=None, *args, **kwargs):
        # add owner class (instance of Field) to owner arg on init.
        self.owner = owner

    def init_config(self):
        pass

    def init_fields(self):
        pass

    def parse_config(self, cfg):
        attrs = configs["field_config"]["attrs"]
        config = parse_config(cfg, attrs, FieldConfig)
        return config

    def parse_fields(self):
        conf = self.owner.config
        model_fields = {
            f.name: f
            for f in getattr(self.owner.model._meta, "fields")
            if not exclude or (exclude and f.name not in exclude)
        }
        fields, exclude = conf.fields, conf.exclude

        # field is either ("name") or ("name")

        if fields:
            if isinstance(fields, str):
                assert fields == "__all__"
                field_instances = [Field()]

    def parse_options(self):
        # print(f"xxxxxxx parse options, {self.owner.config=}, {self.owner.options=}")

        # create blank O object with default values
        options = O()
        defaults = O().to_dict()
        # print("###### options at start", options)
        field = self.owner
        if hasattr(field, "config"):
            # if config is set, overwrite values defined in config
            if hasattr(field.config, "options"):
                options.update(field.config.options)
                if hasattr(field, "options"):
                    new = field.options.to_dict()
                    for k, v in new.items():  # TODO: debug, this does not work yet
                        if v != defaults[k] and v != options.to_dict()[k]:
                            options.update({k: v})

            # if options given in field init, overwrite values again.
            elif hasattr(field, "options"):
                options.update(field.options)

        # print("###### options at end", options)
        return options

    def parse_references(self):
        return "Refrences"


class CollectionParser:
    """
    Helper class that seperates each parsing step into a single staticmethod.

    #TODO considere writing init with model arg, and injecting the parser into the
    class in metaclass. then rewrite staticmethods to normal self.methods.
    """

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.owner = owner

    def parse_config(self, cfg):
        attrs = configs["collection_config"]["attrs"]
        config = parse_config(cfg, attrs, CollectionConfig)
        print(config, self.owner)
        if not hasattr(config, "name") or not config.name:
            print(f"Configuration error. You must set a name attribute for your class.")

        else:
            if not config.name.startswith(col_prefix):
                config.name = col_prefix + config.name

        if not hasattr(config, "queryset") or not config.queryset:
            config.queryset = "objects.all"
        return config

    @staticmethod
    def parse_field_options():
        """
        Parses field options in collection.
        """
        pass

    @staticmethod
    def validate_field_exists(f, model):
        fields = [df.name for df in model._meta.fields]
        # print(f, model, type(f))
        if isinstance(f, str):
            # print("f was string")
            res = f in fields
        else:
            res = f.name in fields
        # print("in validation", f.name, res)
        if res:
            return res
        else:
            print("RAISE ERROR, field not in model fields")
            return res

    @staticmethod
    def resolve_config_fields(model, fields: Iterable = [], exclude: Iterable = []):
        """
        Is called if config contains fields attribute and or exclude atttrs.
        Resolves fields and excludes and returns list of field-tuples (f_name, f_output_type)

        :param fields: _description_
        :type fields: _type_
        :param exclude: _description_
        :type exclude: _type_
        """

        parsed_fields = []
        if fields:
            for f in fields:
                if not f.name in exclude and CollectionParser.validate_field_exists(
                    f, model
                ):
                    parsed_fields.append(f)

        return parsed_fields
