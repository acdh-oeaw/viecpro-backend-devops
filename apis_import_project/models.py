from django.apps import apps
from django.conf import settings
import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from collections import defaultdict
import logging
from django.contrib.auth.models import User
from django.db import models
from reversion.models import Version

from apis_core.apis_entities.models import Institution, AbstractEntity
from apis_core.apis_metainfo.models import Source, Collection, TempEntityClass
# Create your models here.
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import PersonInstitutionRelation

log = logging.getLogger("mylogger")

table_base_name = "apis_import_project"

class DataSource(models.Model):
    """
    Model to represent a single unit of an archival material (book, script etc.) that is used as a source for
    generating or
    updating data.
    Currently, the source is split into pages upon upload, each represented by a DataSourcePage-instance.

    MetaData on the source lives in the DataSource instance. Further MetaData and the editing progress is stored with
    each DataSourcePage instance, in pagedata instances.

    Accessor functions allow traversing related DataSourcePage-objects and to get or set their metadata.
    """

    class Meta: 
        db_table = table_base_name + "_datasource"

    name = models.CharField(max_length=255, blank=False, null=False)
    server_directory = models.CharField(max_length=255, blank=False, null=False)
    page_count = models.IntegerField(blank=True, null=True)  # can be removed and returned as related max
    citation = models.TextField(max_length=600, blank=True, null=True)
    year = models.CharField(max_length=10)
    owner = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

    def get_page_url(self, page_num):
        """
        :param page_num: page_index of page
        :type page_num: int
        :param url: if true, returns url of page
        :type url: bool
        :return: returns string of either path to staticfiles or url
        :rtype: str
        """

        base_path = settings.apis_import_project_IIIF_BASE_URL

        if not base_path.endswith("/"):
            base_path += "/"

        if not self.server_directory.endswith("/"):
            self.server_directory += "/"
            self.save()

        return f"{base_path}{self.server_directory}page_{page_num}.jp2/full/max/0/default.jpg"

    def get_page_object(self, page_num):
        try:
            return DataSourcePage.objects.get(DataSource=self, page_index=int(page_num))
        except ObjectDoesNotExist as e:
            print("Intercepted ObjectDoesNotExist Error, page index out of range:", e)
            return None

    def get_page_token(self, page_num):
        try:
            return DataSourcePage.objects.get(DataSource=self, page_index=page_num).page_token
        except ObjectDoesNotExist as e:
            print("Intercepted ObjectDoesNotExist Error, page index out of range:", e)
            return None

    def set_page_token(self, page_num, page_token):

        page_obj = self.get_page_object(page_num)

        if page_obj:
            page_obj.page_token = page_token
            page_obj.save()
            return True
        else:
            return False

    def set_start_page(self, page_num, page_token):
        page_num = int(page_num)
        page_token = int(page_token)
        start_page = self.get_page_object(page_num)
        log.info(
            f"start_page is {start_page}, token is {page_token}, page_num is {page_num}, curr_page_token is "
            f"{start_page.page_token}")
        start_page.page_token = page_token
        start_page.save()

        while self.get_next_page(page_num):
            page_num += 1
            page_token += 1
            page = self.get_page_object(page_num)
            page.page_token = page_token
            page.save()


    def get_next_page(self, curr_page, direction="next"):
        curr_page = int(curr_page)
        if direction == "next":
            next_page = curr_page + 1
        elif direction == "previous":
            next_page = curr_page - 1
        if 0 < next_page < self.page_count:
            return next_page
        else:
            return None

    def get_pagedata(self, project, page_num=None, page=None):
        if not page:
            page = self.get_page_object(page_num)
        pd = page.get_pagedata(project=project)
        return pd

    def __str__(self):
        return self.name
        # return self.__class__.__name__+".__"+self.name

    def __repr__(self):
        return self.__class__.__name__ + ".__" + self.name

    def get_last_page(self, project, user):
        ds_state = DataSourceProjectState.objects.get(datasource=self, project=project, user=user)
        if ds_state:
            return ds_state.last_page
        else:
            return None

    def set_last_page(self, page, project, user):
        ds_state = DataSourceProjectState.objects.get(datasource=self, project=project, user=user)
        ds_state.last_page = page
        ds_state.save()
        log.info(f"set datasource {self} last page to {page}")


class DataSourcePage(models.Model):
    """
    Model represents a single page of a DataSourceObject. The related DataSource-instances metadata can be accessed
    through methods here.

    Additional MetaData that also stores information on the editing process is kept in instances of PageData objects.

    Note: MetaData that revers to the physical object, like the page_token, is stored in this model. MetaData
    refering to the editing process, and that should be distinguishable between each editor, is stored in an
    PageDataInstance.
    Therefore each DataSourcePage can have multiple PageData relations.

    Fields
    ----
    page_index: Represents the numerical order of the pages and should not be changed, as it is used to index into
    the pages.
    page_token: Lexical page token as appearing on the physical page, i.e. as arabic numerals or roman numerals or
    whatever. Can be set in the editing process. Used in the automatic creation of a citation, together with the
    citation as given in the DataSource.

    todo: link the citation with instances of Work-Objects or Source-Objects
    """


    class Meta: 
        db_table = table_base_name + "_datasourcepage"

    DataSource = models.ForeignKey(DataSource, null=False, blank=False, on_delete=models.CASCADE)
    page_index = models.IntegerField(blank=False, null=False)
    page_token = models.CharField(max_length=20, blank=True, null=True)


    def get_url(self):
        return self.DataSource.get_page_url(self.page_index)

    def get_citation(self):
        return self.DataSource.citation + ", " + self.page_token

    def get_pagedata(self, project):
        pd, c = PageData.objects.get_or_create(page=self, project=project)
        return pd

    def __str__(self):
        return self.__class__.__name__ + ".__page__" + str(self.page_index)


class ImportProject(models.Model):
    """
    Represents an Import-Project, i.e. a collection of DataSources, and Editors that can access these DataSources.
    The Owner can be granted rights to delete the owned project (not implemented yet).
    """
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(max_length=2000, blank=True, null=True, help_text="Describe your project here.")
    owner = models.ForeignKey(User, blank=False, null=True, on_delete=models.SET_NULL, related_name="owner")
    Editors = models.ManyToManyField(User, blank=True, related_name="Editors",
                                     help_text="Add users that should be able to edit this project.")
    DataSources = models.ManyToManyField(DataSource, blank=True,
                                         help_text="Consider adding existing Datasources uploaded by you to this "
                                                   "Project. Or upload/add additional Datasources later.")
    collection = models.ForeignKey(Collection, null=True, blank=True, on_delete=models.SET_NULL)

    # todo: consider adding last edited page here

    class Meta: 
        db_table = table_base_name + "_importproject"

    def save(self, *args, **kwargs):
        if not self.collection:
            col, created = Collection.objects.get_or_create(name=f"Created in {self.name}")
            self.collection = col
        super(ImportProject, self).save(*args, **kwargs)

    def __str__(self):
        return f"ImportProject_{self.name}"

    def get_role(self, user):
        if user == self.owner:
            return "Owner"
        elif user in self.Editors.all():
            return "Editor"
        else:
            return ""

    def get_last_datasource(self, user):
        project_state = ProjectState.objects.get(project=self, user=user)
        if project_state:
            return project_state.last_datasource
        else:
            return None

    def set_last_datasource(self, datasource, user):
        project_state = ProjectState.objects.get(project=self, user=user)
        project_state.last_datasource = datasource
        project_state.save()
        log.info(f"set project {self} last datasource to {datasource}")





class GenericCollectionEntry(models.Model):
    """
    Generic model to allow saving any instance of any given model to a special collection bound to a PageData object.
    Allows to distinguish if an instance of an entity, relation or vocab hast been created or edited within a
    given project.

    The collection is bound to each PageData object to allow to retrieve all edits associated with a certain page for
    review and control purposes.

    todo: connect this with the revision-library. Save the state before the editing process and allow to reset the
    changed fields.
    """
    class Meta: 
        db_table = table_base_name + "_genericcollectionentry"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey("content_type", "id")
    #last_version = models.ForeignKey(Version, null=True, blank=True, on_delete=models.SET_NULL)
    #last_json = models.TextField(blank=True)

    def get_last_version_dict(self, project):
        if self.last_json.filter(project=project).exists():
            last_json = self.last_json.get(project=project).json
        else:
            return None

        if last_json and last_json != "":
            data = json.loads(last_json)
            return data
        else:
            return None

    def get_last_version_dict_with_objects(self, project):
        data = self.get_last_version_dict(self, project)
        if data:
            pass
        # todo: implement generic deserialization of the string values, by restoring the respective objects form the name and id values.

    def get_(self):
        return self.content_object


    def get_tuple(self):
        return (self.content_type, self.content_object)


    def get_tuple_versioned(self, project):
        return (self.content_type, (self.content_object, self.get_last_version_dict(project=project)))

    def get_obj(self):
        return self

    @classmethod
    def create(cls, obj):
        if GenericCollectionEntry.objects.filter(id=obj.id).exists():
            instance = GenericCollectionEntry.objects.get(id=obj.id)
        else:
            instance = GenericCollectionEntry.objects.create(content_object=obj)
        return instance

class ProjectCollectionEntry(models.Model):

    class Meta: 
        db_table = table_base_name + "_projectcollectionentry"

    json = models.TextField(blank=True)
    project = models.ForeignKey(ImportProject, null=True, on_delete=models.CASCADE)
    entry = models.ForeignKey(GenericCollectionEntry, null=False, blank=False, on_delete=models.CASCADE, related_name="last_json")

class PageCollection(models.Model):
    """
    A collection of generic instances of any kind that tracks if the instance was edited or created within a project.
    See GenericCollectionEntry docstring for more information.
    """

    class Meta: 
        db_table = table_base_name + "_pagecollection"

    created_in = models.ManyToManyField(GenericCollectionEntry, related_name="created")
    edited_in = models.ManyToManyField(GenericCollectionEntry, related_name="edited")


class PageData(models.Model):
    """
    Stores metadata on the editing process for each page within a given project.

    See PageCollection for the generic functionality of the collection field.

    Accessor methods and properties allow to interface with the data held in the collection.
    todo: consider moving the accessor methods to a custom manager.

    Note:
    A Viecpro specific implementation - allowing to track last written institution and function per page, to prefill
    the PersonInstituion form. This is not only viecpro specific, but also specific for a special kind of DataSource
    (Hofstaatsschematismen).

    todo: could be refactored to make this specific behaviour managed via some sort of settings-file. And to make
        some sort of generic solution for implementing other specific, but similiar functionality.
    """
    class Meta: 
        db_table = table_base_name + "_pagedata"

    project = models.ForeignKey(ImportProject, blank=False, null=False, on_delete=models.CASCADE)
    page = models.ForeignKey(DataSourcePage, blank=False, null=False, on_delete=models.CASCADE)
    # todo: NOT GENERIC
    # todo: make this generic to allow for saving of other fields.
    institution = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.SET_NULL)
    function = models.ForeignKey(PersonInstitutionRelation, null=True, blank=True, on_delete=models.SET_NULL)
    collection = models.OneToOneField(PageCollection, auto_created=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        # Create PageCollection on save (also init) if one doesn't exist yet.
        if not self.collection:
            col = PageCollection.objects.create()
            self.collection = col
        super(PageData, self).save(*args, **kwargs)

    def get_edited(self):
        res = self.collection.edited_in.all()
        if res:
            return [entry.get_() for entry in res]
        else:
            return None

    def get_edited_tuple(self):
        res = self.collection.edited_in.all()
        if res:
            return [entry.get_tuple() for entry in res]
        else:
            return None

    def get_edited_tuple_with_version(self, project):
        res = self.collection.edited_in.all()
        if res:
            return [entry.get_tuple_versioned(project=project) for entry in res]
        else:
            return None

    def get_created(self):
        res = self.collection.created_in.all()
        if res:
            return [entry.get_() for entry in res]
        else:
            return None

    def get_created_tuple(self):
        res = self.collection.created_in.all()
        if res:
            return [entry.get_tuple() for entry in res]
        else:
            return None

    def get_all(self):
        a, b = None, None
        #if self.collection.created_in:
        a = list(self.collection.created_in.all())
        #if self.collection.edited_in:
        b = list(self.collection.edited_in.all())

        if a and b:
            res = a + b
        elif a:
            res = a
        elif b:
            res = b
        else:
            res = []

        return res

    def get_full_collection_dict(self):
        try:
            tuples = self.get_created_tuple() + self.get_edited_tuple()
            res = defaultdict(list)

            for ctype, cobj in tuples:
                res[ctype].append(cobj)

            return dict(res)

        except:
            return {}

    def get_edited_dict(self):
        tuples = self.get_edited_tuple()
        res = defaultdict(list)
        if tuples:
            for ctype, cobj in tuples:
                res[ctype].append(cobj)

        return dict(res)

    def get_created_dict(self):
        # todo: fix these sections here
        tuples = self.get_created_tuple()
        res = defaultdict(list)
        if tuples:
            for ctype, cobj in tuples:
                res[ctype].append(cobj)

        return dict(res)

    def get_full_collection_dict_named(self):
        try:

            tuples = self.get_created_tuple() + self.get_edited_tuple()
            res = defaultdict(list)

            for ctype, cobj in tuples:
                k = ctype.model_class().__name__
                res[k].append(cobj)

            return dict(res)

        except:
            return {}

    def get_edited_dict_named(self):
        tuples = self.get_edited_tuple()
        res = defaultdict(list)
        if tuples:
            for ctype, cobj in tuples:
                k = ctype.model_class().__name__

                res[k].append(cobj)

        return dict(res)

    def get_edited_dict_named_with_version(self, project):
        tuples = self.get_edited_tuple_with_version(project=project)
        res = defaultdict(list)
        if tuples:
            for ctype, version_tup in tuples:
                print(len(version_tup), version_tup)
                k = ctype.model_class().__name__

                res[k].append(version_tup)

        return dict(res)

    def get_created_dict_named(self):
        tuples = self.get_created_tuple()
        res = defaultdict(list)
        if tuples:
            for ctype, cobj in tuples:
                k = ctype.model_class().__name__
                res[k].append(cobj)

        return dict(res)

    @property
    def edited(self):
        return self.get_edited()

    @property
    def created(self):
        return self.get_created()


    def add_to_edited(self, obj, serialization=None, project=None):
        if project:
            serialization["version"] = "original"
            log.info(f"CALLED")
            col_entity = GenericCollectionEntry.create(obj)
            log.info(f"last json for {col_entity}, was: '{col_entity.last_json}'")
            if not col_entity.last_json.filter(project=project).exists(): # or col_entity.last_json in ["null", "", None, "false", False, "none", "None"]: # is None or col_entity.last_json == "" or col_entity.last_json:
                data_str = json.dumps(serialization)
                pce = ProjectCollectionEntry.objects.create(json=data_str, entry=col_entity, project=project)
                pce.save()
                #col_entity.last_json.add(pce)
                #col_entity.save()
                log.info(f"saved serialization for {col_entity}, data: {data_str}")

            if col_entity not in self.collection.edited_in.all():
                self.collection.edited_in.add(col_entity)
                log.info(f"added: {obj} to collection: {self.collection} in pagedata: {self}")



    def add_to_edited_old(self, obj):
        """

        :param obj: instance of any apis model. Intended use is only for relations, vocabs and entities.
        :type obj: instance
        :return:
        :rtype:
        """
        versions = Version.objects.get_for_object(obj)
        last_version = None
        if versions:
            if len(versions) > 1:
                last_version = versions[1]
            else:
                try:
                    obj.save()
                    versions = Version.objects.get_for_object(obj)
                    last_version = versions[1]
                except:
                    last_version = versions[0]

                    log.info(f"couldn't get latest version, set version to version {last_version} for {obj}, id={obj.id}")

        #ex = GenericCollectionEntry.objects.filter(id=obj.id).exists()
        col_entity = GenericCollectionEntry.create(obj)

        # todo: check that this works!
        if not col_entity.last_version:
            log.info(f"col_entry {col_entity} didn't exist, latest version set to {last_version}")
            col_entity.last_version = last_version
            col_entity.save()

        if col_entity not in self.collection.edited_in.all():
            self.collection.edited_in.add(col_entity)
            log.info(f"added: {obj} to collection: {self.collection} in pagedata: {self}")

    def add_to_created(self, obj):
        col_entity = GenericCollectionEntry.create(obj)
        if col_entity not in self.collection.created_in.all():
            self.collection.created_in.add(col_entity)
            log.info(f"added: {obj} to collection: {self.collection} in pagedata: {self}")


class DataSourceProjectState(models.Model):
    """
    Stores the state a DataSource is in during the editing process, on per-user basis and in relation to a specific
    project. For now it only keeps the
    last_page that was edited, to reload it when continuing an edit.
    """

    class Meta: 
        db_table = table_base_name + "_datasourceprojectstate"

    datasource = models.ForeignKey(DataSource, blank=False, null=True, on_delete=models.CASCADE)
    project = models.ForeignKey(ImportProject, blank=False, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE)
    last_page = models.ForeignKey(DataSourcePage, blank=True, null=True, on_delete=models.SET_NULL)


class ProjectState(models.Model):
    """
    Stores the state a Project is in during the editing process, on per-user basis. For now it only keeps the last
    DataSource to reload it when continuing an edit.
    """
    class Meta: 
        db_table = table_base_name + "_projectstate"

    project = models.ForeignKey(ImportProject, blank=False, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE)
    last_datasource = models.ForeignKey(DataSource, blank=True, null=True, on_delete=models.SET_NULL)
