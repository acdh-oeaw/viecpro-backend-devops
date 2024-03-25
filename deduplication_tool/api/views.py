from rest_framework import viewsets, filters # type: ignore
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from dubletten_tool.models import Group, PersonProxy
from apis_core.apis_entities.models import Person
from . serializers import DedupPersonSerializer, DedupGroupObjectSerializer, DedupGroupListSerializer, DedupPersonProxySerializer

class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    filter_backends=[filters.SearchFilter, DjangoFilterBackend]
    serializer_class = DedupPersonSerializer
    search_fields = ["name", "first_name"]
    filter_fields = ["gender"]
    ordering_fields = ["name", "first_name"]

class SingleListViewSet(PersonViewSet):
    queryset = Person.objects.filter(personproxy__status="single")


class DublettenViewSet(PersonViewSet):
    queryset = Person.objects.filter(personproxy__status="candidate")

class GroupObjectViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends=[filters.SearchFilter, DjangoFilterBackend]
    queryset = Group.objects.all().prefetch_related("members")
    serializer_class=DedupGroupObjectSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]

class GroupListViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends=[filters.SearchFilter, DjangoFilterBackend]
    queryset = Group.objects.all()
    serializer_class = DedupGroupListSerializer
    search_fields = ["name"]
    filter_fields = ["_gender"]
    ordering_fields = ["name"]


class PersonProxyViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends=[filters.SearchFilter, DjangoFilterBackend]
    queryset = PersonProxy.objects.all().prefetch_related("person")
    serializer_class = DedupPersonProxySerializer
    search_fields = ["person__name", "person__first_name"]
    ordering_fields = ["person__name", "person__first_name"]
    filter_fields = ["person__id"]

class SingleObjectViewSet(PersonProxyViewSet):
    queryset = PersonProxy.objects.filter(status="single").prefetch_related("person")