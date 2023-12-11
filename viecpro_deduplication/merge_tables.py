import django_tables2 as tables
from django.utils.safestring import mark_safe
from django_tables2.utils import A
from django.db.models import Case, When
from apis_core.apis_relations.models import PersonPerson
from django.conf import settings

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_metainfo.tables import (
    generic_order_start_date_written,
    generic_order_end_date_written,
    generic_render_start_date_written,
    generic_render_end_date_written
)


input_form = """
  <input type="checkbox" name="keep" value="{}" title="keep this"/> |
  <input type="checkbox" name="remove" value="{}" title="remove this"/>
"""

empty_text_default = 'There are currently no relations'


class VorfinListTable(tables.Table):

    def render_name(self, record, value):
        if value == "":
            return "(No name provided)"
        else:
            return value
    entity = "Person"
    # reuse the logic for ordering and rendering *_date_written
    # Important: The names of these class variables must correspond to the column field name,
    # e.g. for start_date_written, the methods must be named order_start_date_written and render_start_date_written
    order_start_date_written = generic_order_start_date_written
    order_end_date_written = generic_order_end_date_written
    render_start_date_written = generic_render_start_date_written
    render_end_date_written = generic_render_end_date_written

    name = tables.LinkColumn(
        'viecpro_deduplication:vorfin_detail',  # todo: change to local detail view
        args=[entity.lower(), A('pk')],
        empty_values=[]
    )
    export_formats = [
        'csv',
        'json',
        'xls',
        'xlsx',
    ]

    class Meta:
        model = AbstractEntity.get_entity_class_of_name(entity_name="person")
        default_cols = ["name", "first_name",
                        "start_date_written", "end_date_written"]

        fields = default_cols
        attrs = {"class": "table table-hover table-striped table-condensed"}

        # quick ensurance if column is indeed a field of this entity
        for col in default_cols:
            if not hasattr(model, col):
                raise Exception(
                    f"Could not find field in entity:Person\n"
                    f"of column (probably defined in 'table_fields' settings): {col}\n"
                )

    def __init__(self, *args, **kwargs):
        if "apis_ampel" in settings.INSTALLED_APPS:
            from apis_ampel.helper_functions import is_ampel_active
            if is_ampel_active("person"):
                self.base_columns['ampel'] = tables.TemplateColumn(
                    template_name="ampel/ampel_template_column.html", verbose_name="Ampel")

        super().__init__(*args, **kwargs)


def get_generic_relations_table(relation_class, entity_instance, detail=None):
    """
    Creates a table class according to the relation and entity class given by the parameters.

    :param relation_class: the class where the entity_instance can have instantiated relations to
    :param entity_instance: the entity instance of which related relations and entities are to be displayed
    :param detail: boolean : if this Table is to be displayed in an detail or edit UI
    :return: a django-tables2 Table Class tailored for the respective relation class and entity instance
    """

    # create all variables which save the foreign key fields which are different for each relation class
    entity_class_name = entity_instance.__class__.__name__.lower()
    related_entity_class_name_a = relation_class.get_related_entity_classA().__name__.lower()
    related_entity_class_name_b = relation_class.get_related_entity_classB().__name__.lower()
    related_entity_field_name_a = relation_class.get_related_entity_field_nameA()
    related_entity_field_name_b = relation_class.get_related_entity_field_nameB()

    # find out what other entity class the current entity instance in a given relation class is related to
    # (needed for linkg towards instances of related entities)
    if entity_class_name == related_entity_class_name_a == related_entity_class_name_b:
        other_related_entity_class_name = entity_class_name

    elif entity_class_name == related_entity_class_name_a:
        other_related_entity_class_name = related_entity_class_name_b

    elif entity_class_name == related_entity_class_name_b:
        other_related_entity_class_name = related_entity_class_name_a

    else:
        raise Exception(
            "Did not find the entity instance in the given relation class fields!" +
            "Either a wrong entity instance or wrong relation class was passed to this function."
        )

    class RelationTableBase(tables.Table):
        """
        The base table from which detail or edit tables will inherit from in order to avoid redundant definitions
        """

        # reuse the logic for ordering and rendering *_date_written
        # Important: The names of these class variables must correspond to the column field name,
        # e.g. for start_date_written, the methods must be named order_start_date_written and render_start_date_written
        order_start_date_written = generic_order_start_date_written
        order_end_date_written = generic_order_end_date_written
        render_start_date_written = generic_render_start_date_written
        render_end_date_written = generic_render_end_date_written

        class Meta:
            """
            Meta class needed for django-tables2 plugin.
            """

            empty_text = empty_text_default
            model = relation_class
            print("model is", model)

            # the fields list also serves as the defining order of them, as to avoid duplicated definitions
            fields = [
                'start_date_written',
                'end_date_written',
                'other_relation_type',
                "other_related_entity"
            ]
            # reuse the list for ordering
            sequence = tuple(fields)

            # This attrs dictionary I took over from the tables implementation before. No idea if and where it would be needed.
            attrs = {
                "class": "table table-hover table-striped table-condensed",
                "id": related_entity_class_name_a.title()[:2] + related_entity_class_name_b.title()[:2] + "_conn"
            }

        def render_other_related_entity(self, record, value):
            """
            Custom render_FOO method for related entity linking. Since the 'other_related_entity' is a generated annotation
            on the queryset, it does not return the related instance but only the foreign key as the integer it is.
            Thus fetching the related instance is necessary.

            :param record: The 'row' of a queryset, i.e. an entity instance
            :param value: The current column of the row, i.e. the 'other_related_entity' annotation
            :return: related instance
            """

            if value == record.get_related_entity_instanceA().pk:
                return record.get_related_entity_instanceA()

            elif value == record.get_related_entity_instanceB().pk:
                if relation_class == PersonPerson:
                    return str(record.get_related_entity_instanceB())+f" [{record.get_related_entity_instanceB().id}]"
                else:
                    return record.get_related_entity_instanceB()

            else:
                raise Exception(
                    "Did not find the entity this relation is supposed to come from!" +
                    "Something must have went wrong when annotating for the related instance."
                )

        def __init__(self, data, *args, **kwargs):

            # annotations for displaying data about the 'other side' of the relation.
            # Both of them ('other_related_entity' and 'other_relation_type') are necessary for displaying relations
            # in context to what entity we are calling this from.
            data = data.annotate(
                # In order to provide the 'other instance' for each instance of a table where this whole logic is called from,
                # the queryset must be annotated accordingly. The following Case searches which of the two related instances
                # of a relation queryset entry is the one corresponding to the current entity instance. When found, take the
                # other related entity (since this is the one we are interested in displaying).
                #
                # The approach of using queryset's annotate method allows for per-instance case decision and thus
                # guarantees that the other related entity is always correctly picked,
                # even in case two entities are of the same class.
                other_related_entity=Case(
                    # **kwargs pattern is needed here as the key-value pairs change with each relation class and entity instance.
                    When(**{
                        related_entity_field_name_a + "__pk": entity_instance.pk,
                        "then": related_entity_field_name_b
                    }),
                    When(**{
                        related_entity_field_name_b + "__pk": entity_instance.pk,
                        "then": related_entity_field_name_a
                    }),
                )
            ).annotate(
                # Get the correct side of the relation type given the current entity instance.
                #
                # The approach of using queryset's annotate method allows for per-instance case decision and thus
                # guarantees that the other related entity is always correctly picked,
                # even in case two entities are of the same class.
                other_relation_type=Case(
                    When(**{
                        # A->B relation and current entity instance is A, hence take forward name
                        related_entity_field_name_a + "__pk": entity_instance.pk,
                        "then": "relation_type__name"
                    }),
                    When(**{
                        # A->B relation and current entity instance is B, hence take reverse name.
                        related_entity_field_name_b + "__pk": entity_instance.pk,
                        "then": "relation_type__name_reverse"
                    }),
                )
            )
            for an in data:
                if getattr(an, f"{related_entity_field_name_a}_id") == entity_instance.pk:
                    an.other_relation_type = getattr(an.relation_type, "label")
                else:
                    an.other_relation_type = getattr(
                        an.relation_type, "label_reverse")

            super().__init__(data, *args, **kwargs)

    if detail:

        class RelationTableDetail(RelationTableBase):
            """
            Sublcass inheriting the bulk of logic from parent. This table is used for the 'detail' views.
            """

            def __init__(self, data, *args, **kwargs):
                print("in table detail relationtable, data is:", data)

                # Only addition with respect to parent class is which main url is to be used when clicking on a
                # related entity column.
                self.base_columns["other_related_entity"] = tables.LinkColumn(
                    'apis:apis_entities:generic_entities_detail_view',
                    args=[
                        other_related_entity_class_name,
                        A("other_related_entity")
                    ],
                    verbose_name="Related " + other_related_entity_class_name.title()
                )

                if "apis_ampel" in settings.INSTALLED_APPS:
                    from apis_ampel.helper_functions import is_ampel_active

                    if is_ampel_active(relation_class.__name__):
                        self.base_columns['ampel'] = tables.TemplateColumn(
                            template_name="ampel/edit_inline_table_column.html", verbose_name="Ampel")

                super().__init__(data=data, *args, **kwargs)

        return RelationTableDetail

    else:

        class RelationTableEdit(RelationTableBase):
            """
            Sublcass inheriting the bulk of logic from parent. This table is used for the 'edit' view.
            """

            class Meta(RelationTableBase.Meta):
                """
                Additional Meta fields are necessary for editing functionalities
                """

                # This fields list also defines the order of the elements.
                fields = ["delete"] + RelationTableBase.Meta.fields + ["edit"]

                if 'apis_bibsonomy' in settings.INSTALLED_APPS:
                    fields = ["ref"] + fields

                # again reuse the fields list for ordering
                sequence = tuple(fields)

            def __init__(self, *args, **kwargs):

                # Clicking on a related entity will lead also the edit view of the related entity instance
                self.base_columns["other_related_entity"] = tables.LinkColumn(
                    'apis:apis_entities:generic_entities_edit_view',
                    args=[
                        other_related_entity_class_name, A(
                            "other_related_entity")
                    ],
                    verbose_name="Related " + other_related_entity_class_name.title()
                )

                # delete button
                self.base_columns['delete'] = tables.TemplateColumn(
                    template_name='apis_relations/delete_button_generic_ajax_form.html'
                )

                # edit button
                self.base_columns['edit'] = tables.TemplateColumn(
                    template_name='apis_relations/edit_button_generic_ajax_form.html'
                )

                # bibsonomy button
                if 'apis_bibsonomy' in settings.INSTALLED_APPS:
                    self.base_columns['ref'] = tables.TemplateColumn(
                        template_name='apis_relations/references_button_generic_ajax_form.html'
                    )

                super().__init__(*args, **kwargs)

        return RelationTableEdit
