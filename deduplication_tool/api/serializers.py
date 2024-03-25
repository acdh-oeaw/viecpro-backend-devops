from rest_framework import serializers # type: ignore
from apis_core.apis_entities.models import Person, Institution
from apis_core.apis_relations.models import PersonInstitution, PersonPerson
from apis_core.apis_vocabularies.models import PersonInstitutionRelation
from dubletten_tool.models import Group, PersonProxy



class DedupPersonSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Person
        fields = ["id","name", "first_name", "gender", "start_date", "end_date"]


class DedupInstitutionSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Institution
        fields = ["id","name",  "start_date", "end_date"]

class DedupRersonInstitutionRelationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PersonInstitutionRelation
        fields = ["id", "name", "name_reverse"]
 

class DedupPersonInstitutionSerializer(serializers.ModelSerializer): 
    relation_type = DedupRersonInstitutionRelationSerializer(many=False, read_only=True)
    related_person = DedupPersonSerializer(many=False, read_only=True)
    related_institution = DedupInstitutionSerializer(many=False, read_only=True)
    
    class Meta: 
        model = PersonInstitution
        fields = ["id", "relation_type", "related_person", "related_institution", "start_date", "end_date"]


class DedupPersonPersonSerializer(serializers.Serializer):
    class Meta:
        model = PersonPerson
        fields = ["id", "related_personA", "related_personB", "start_date", "end_date"]


class DedupPersonProxySerializer(serializers.ModelSerializer):
    person = DedupPersonSerializer(many=False, read_only=True)
    relations = DedupPersonInstitutionSerializer(source="person.personinstitution_set", many=True, read_only=True)

    class Meta:
        model = PersonProxy
        fields = ["status", "person", "relations"]

class DedupGroupObjectSerializer(serializers.ModelSerializer):
    members = DedupPersonProxySerializer(many=True, read_only=True)
    vorfin = DedupPersonSerializer(many=False, read_only=True)
    
    class Meta: 
        model = Group
        fields = ["id", "name", "vorfin", "members"]
        
class DedupGroupListSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(source="_gender")

    class Meta: 
        model = Group
        fields = ["id", "name", "gender", "count"]

