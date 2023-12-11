import re

from django.conf import settings
from django.db.models.query import QuerySet
from django.urls import reverse
from rest_framework import serializers
from apis_core.apis_labels.serializers import LabelSerializerLegacy as LabelSerializer
from apis_core.apis_entities.serializers_generic import VocabsSerializer

base_uri = getattr(settings, "APIS_BASE_URI", "http://apis.info")
if base_uri.endswith("/"):
    base_uri = base_uri[:-1]

class EntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    labels = LabelSerializer(source="label_set", many=True)

    def add_entity_type(self, obj):
        return str(obj.__class__.__name__)


    def __init__(
        self, *args, **kwargs
    ):
        super(EntitySerializer, self).__init__(*args, **kwargs)
        if type(self.instance) == QuerySet:
            inst = self.instance[0]
        else:
            inst = self.instance
        if inst is None:
            return
        for f in inst._meta.fields:
            field_name = re.search(r"([A-Za-z]+)\'>", str(f.__class__)).group(1)
            if field_name in [
                "CharField",
                "DateField",
                "DateTimeField",
                "IntegerField",
                "FloatField",
            ]:
                self.fields[f.name] = getattr(serializers, field_name)()
            elif field_name in ["ForeignKey", "ManyToMany"]:
                if str(f.related_model.__module__).endswith("apis_vocabularies.models"):
                    many = False
                    if f.many_to_many or f.one_to_many:
                        many = True
                    self.fields[f.name] = VocabsSerializer(many=many)
        for f in inst._meta.many_to_many:
            if f.name.endswith("relationtype_set"):
                continue
            elif f.name == "collection":
                pass
            elif str(f.related_model.__module__).endswith("apis_vocabularies.models"):
                self.fields[f.name] = VocabsSerializer(many=True)
        self.fields["entity_type"] = serializers.SerializerMethodField(
            method_name="add_entity_type"
        )



class RelationEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_date_written = serializers.DateField()
    end_date_written = serializers.DateField()
    relation_type = serializers.SerializerMethodField(method_name="add_relation_label")



    def add_entity(self, obj):
        return EntitySerializer(
            getattr(obj, "related_{}".format(self.entity_type)), depth_ent=0
        ).data

    def add_relation_label(self, obj):
        cm = obj.__class__.__name__
        res_1 = dict()
        res_1["id"] = obj.relation_type.pk
        res_1[
            "url"
        ] = f"{base_uri}{reverse('apis_core:apis_api:{}relation-detail'.format(cm).lower(), kwargs={'pk': obj.relation_type.pk},)}"
        if self.reverse and len(obj.relation_type.label_reverse) > 0:
            res_1["label"] = obj.relation_type.label_reverse
        elif self.reverse:
            res_1["label"] = "({})".format(obj.relation_type.label)
        else:
            res_1["label"] = obj.relation_type.label
        return res_1

    def __init__(self, *args, own_class=None, reverse=False, **kwargs):
        super(RelationEntitySerializer, self).__init__(*args, **kwargs)
        self.own_class = own_class
        self.reverse = reverse
        if self.instance is not None:
            for f in self.instance._meta.fields:
                if f.name.startswith("related_"):
                    mk2 = f.name.replace("related_", "")

                    if mk2.lower() != own_class.lower():
                        self.entity_type = mk2
                        self.fields["target"] = serializers.SerializerMethodField(
                            method_name="add_entity"
                        )
