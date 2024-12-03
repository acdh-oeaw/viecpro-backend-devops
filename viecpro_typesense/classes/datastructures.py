from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class O:
    """ """

    index: bool = True
    optional: bool = False
    facet: bool = False
    sort: bool = False
    type: str = "string"  # TODO: implement mechanism to set type to internal db type map of dj_field if none
    token_separators: list | None = None
    # set default to none and check when field is initialised what the type of the handler or the django field is

    def to_dict(self):
        return {
            k: v for k, v in asdict(self).items()
        }  # todo: remove unpacking, this is redundant

    def update(self, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                else:
                    raise Exception(
                        f"Tried to merge your O-object with attributes not allowd in O."
                    )

        elif isinstance(data, O):
            self.update(data.to_dict())


field_type_map = {}

default_handlers = {}
