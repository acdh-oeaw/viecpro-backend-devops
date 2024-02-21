from django.db.models.query_utils import DeferredAttribute
from django.db.models.fields import Field as DJ_FIELD
from .field_meta import FieldMeta
from typing import List, Iterable, Callable, Union
from . import O
from .parsers import FieldParser
import inspect

# TODO: set metaclass to CollectionMeta
# TODO: remove metaclass and set FieldTemplate as superclass


class Field(metaclass=FieldMeta):
    """ """

    # Consider allowing options as Union(dict, O), and add parsing logic for that if implemented
    # removed: :Union(Iterable[str], str) on references
    def __init__(
        self,
        references,
        options: O = O(),
        handler=None,
        verbose_name=None,
        pass_instance=False,
        *args,
        **kwargs,
    ):
        """
   
        """
        self._references: Union(
            str, Iterable[str]
        ) = references  # TODO: new name for referenced field names
        self.name: str = verbose_name
        self.options: O = options
        self.handler = handler if handler else self.config.handler
        self._parser: FieldParser = FieldParser(owner=self)
        self.pass_instance = pass_instance

    def __get__(self, inst, owner):
        # print(f"Field __get__ for {self=}. {inst=}, {owner=}")
        if inst is None:
            return self
        else:
            raise Exception(
                "Accessed field descriptor with instance and owner as: ", inst, owner
            )

    def __set_name__(self, owner, name):
        """

        """
        if not hasattr(self, "name") or not self.name:
            self.name = name

        if not isinstance(self, StaticField):
            if hasattr(owner, "config"):
                print(
                    f"set self.__model to {owner.config.model=} for {self=} in collection {owner=}"
                )
                self.x_model = owner.config.model
            else:
                raise Exception("owner had no Config attr")

    def _deferred_init(self):
        """
        Runs rest of the init after the field instance was initialised in Collection class, and received
        the collections model via the CollectionMeta - setup.

        Initialises django fields, params, additional config attrs and options.
        """
        # TODO refactor: handler receives paramas from field, not other way around!

        parser = self._parser

        # parse options
        self.options = parser.parse_options()

        # parse references (field params)
        # self._references = parser.parse_references()

        # move this in parse config
        self._model_fields = {f.name: f for f in self.config.model._meta.fields}

        # TODO: make non-private
        self._references = self.parse_references()

        from . import Handler

        # don't use isinstance here, if Handlers are coded as classes not instances!
        if inspect.isclass(self.handler) and issubclass(self.handler, Handler):
            # if handler is already handler, all good
            pass

        elif callable(self.handler):
            # if handler is a callbel object, wrap a propper handler around it
            # this does shift the definition of the allowed funcs in handler to be callables
            name = self.name + "Handler"
            attrs = {"func": self.handler}
            # this constructs a new handler CLASS not an instance!
            self.handler = type(name, (Handler,), attrs)
        else:
            if not self.handler:
                self.handler = type(
                    self.name + "Handler", (Handler,), {"func": lambda x: x}
                )
            else:
                raise Exception(
                    f"Handler arg was neither a subclass of Handler nor a callable {self.handler=}, {type(self.handler)=}, {self=}"
                )

    def parse_references(self):
        if isinstance(self._references, str):
            #assert (
            #    self._references in self._model_fields.keys()
            #), f"Field {self._references} not in {self._model_fields.keys()}"
            return (self._references,)

        elif isinstance(self._references, (tuple, list, set)):
            for ref in self._references:
                assert isinstance(ref, str) and ref in self._model_fields.keys()
                pass
            return tuple(self._references)

    def parse_dj_fields(self, dj_field):
        if dj_field:
            if isinstance(dj_field, DJ_FIELD):
                return dj_field
            elif isinstance(dj_field, (tuple, list, set)):
                res = []
                for el in dj_field:
                    res.append(self.parse_dj_fields(el))
                return res
            elif isinstance(dj_field, str):
                if dj_field in self.config.model_field_names:
                    return getattr(self.config.model, dj_field)
                else:
                    pass
        else:
            raise Exception("no field given")

    def __str__(self):
        return f"<dtsField: '{self.name}'>"

    def __repr__(self):
        return self.__str__()

    def schema(self):
        """
        Generates the typesense schema entry for this field.


        :return: Typesense field schemea entry as a dict.
        :rtype: dict
        """
        result = {}
        result["name"] = self.name

        if hasattr(self, "options"):
            result.update(self.options.to_dict())
            return result

        else:
            raise Exception("Field had no options attribute", self)

    def get_doc(self, data):
        """
        Runs the actual conversion
        data is the an instance of a model.
        """

        if hasattr(self, "handler"):
            if not self.pass_instance:
                params = [getattr(data, p) for p in self._references]
            else:
                params = [data]

            return self.handler.handle(*params)
        else:
            if isinstance(self._references, (tuple, list, set)):
                raise Exception("Implementation error, this branch is has no body")

            elif isinstance(self._references, DeferredAttribute):
                raise Exception("this case should no longer occur")
                return getattr(data, self.field.field.name)

            else:
                return data


class StaticField(Field, metaclass=FieldMeta):
    def __init__(self, value: any, options: O = O()):
        self.value = value
        self._parser = FieldParser(owner=self)
        self.options = options
        self.options = self._parser.parse_options()

    def get_doc(self, _data):
        return self.value

    def schema(self):
        return {"name": self.name, **self.options.to_dict()}
