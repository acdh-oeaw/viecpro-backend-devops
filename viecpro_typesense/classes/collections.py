import os

from .collection_meta import CollectionMeta

class Collection(metaclass=CollectionMeta):
    """

    """
    

    
    @classmethod
    def schema(cls:"Collection"):
        """


        """
   
  
        result = {}
        result["name"] = cls.config.name
        result["enable_nested_fields"] = cls.config.nested
        result["fields"] = [f.schema() for f in cls.fields]
        return result
    
    
    @classmethod
    def _get_docs(cls, qs=None):
        """

        """


        if not qs:
            qs = cls.config.queryset()
        if num := os.environ.get("NUM", False):
            qs = qs[:int(num)]

        result = []

        from apis_core.apis_metainfo.models import Collection
        vorfinale_eintraege = Collection.objects.get(name="Vorfinale Einträge")
        dubletten = Collection.objects.get(name="Dubletten")
        for inst in qs:
            if hasattr(inst, "collection"):
                if vorfinale_eintraege in inst.collection.all():
                    if hasattr(inst, "ampel"):
                        if inst.ampel.status == "red":
                            continue
                if dubletten in inst.collection.all():
                    continue
            result.append({f.name: f.get_doc(inst) for f in cls.fields})
        
        return result
  





class CollectionAdapter:
    def __init__(self, name, collections=[], fields=[], nested=False):
        self.name = name
        self.collections = collections
        self.fields = fields
        self.nested = nested

    def add_collection(self, collection):
        self.collections.append(collection)

    def add_field(self, field):
        self.fields.append(field)

    def schema(self):
        result = {}
        result["name"] = self.name
        result["enable_nested_fields"] = self.nested
        result["fields"] = [f.schema() for f in self.fields]
        return result

    def _get_docs(self):
        res = []
        for collection in self.collections:
            res += collection._get_docs()
        return res