from .base import *
import re
import dj_database_url
import os

REDIS_HOST = "redis"
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = 'django-db'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


APIS_LIST_VIEWS_ALLOWED = False
APIS_DETAIL_VIEWS_ALLOWED = False
FEATURED_COLLECTION_NAME = "FEATURED"

APIS_BASE_URI = "https://viecpro.acdh.oeaw.ac.at/"


APIS_SKOSMOS = {
    "url": os.environ.get("APIS_SKOSMOS", "https://vocabs.acdh-dev.oeaw.ac.at"),
    "vocabs-name": os.environ.get("APIS_SKOSMOS_THESAURUS", "apisthesaurus"),
    "description": "Thesaurus of the APIS project. Used to type entities and relations.",
}

ALLOWED_HOSTS = re.sub(
    r"https?://",
    "",
    os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,viecpro-dev.acdh-dev.oeaw.ac.at,.acdh-cluster.arz.oeaw.ac.at,viecpro-dev-main.acdh-cluster-2.arz.oeaw.ac.at"),

).split(",")


# You need to allow '10.0.0.0/8' for service health checks.
ALLOWED_CIDR_NETS = ["10.0.0.0/8", "127.0.0.0/8"]

CSP_DEFAULT_SRC = CSP_DEFAULT_SRC + \
    ("sharonchoong.github.io", "github.com/devongovett")

DEBUG = True
DEV_VERSION = False

SPECTACULAR_SETTINGS["COMPONENT_SPLIT_REQUEST"] = True
SPECTACULAR_SETTINGS["COMPONENT_NO_READ_ONLY_REQUIRED"] = True


INSTALLED_APPS += ["django_extensions", "apis_import_project","apis_bibsonomy", "apis_ampel",
                   "dubletten_tool", "viecpro_hierarchy", "viecpro_typesense", "viecpro_typesense_detail", "django_celery_results"]


DATABASES = {"default":
             {
                 "ENGINE": "django.db.backends.mysql",
                 "NAME": os.getenv('MYSQL_DATABASE'),
                 "USER": os.getenv('MYSQL_USER'),
                 "PASSWORD": os.getenv('MYSQL_PASSWORD'),
                 "HOST": os.getenv("MYSQL_HOST"),
                 "PORT": "3306",
             }}


LANGUAGE_CODE = "de"


APIS_RELATIONS_FILTER_EXCLUDE = [
    "*uri*",
    "*tempentityclass*",
    "user",
    "*__id",
    "*source*",
    "label",
    "*temp_entity*",
    "*collection*",
    "*published*",
    "*_set",
    "*_set__*"
    "_ptr",
    "baseclass",
    "*id",
    "*written*",
    "*__text*",
    "text*",
    "*annotation_set_relation*",
    "*start_start_date*",
    "*end_end_date*",
    "*start_end_date*",
    "*end_start_date*",
    "*label*",
    "*review*",
    "*__status",
    "*__references",
    "*__notes",
]
INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

APIS_RELATIONS_FILTER_EXCLUDE += ["annotation", "annotation_set_relation"]

viecpro_hierarchy_BASE_URI = "https://viecpro-dev.acdh-dev.oeaw.ac.at/"


####### ROBOTS.TXT HANDLING #######

# robots.txt file needs to be located in a folder that is registered as a template-dir
# both the end of the url from where the file is served as well as the file itself needs to be named robots.txt
# if you want to add your own robots txt, create a new folder in the root directory and register it here

# replace the path to the folder in which the robots.txt file is to be found here
ROBOTS_TXT_FOLDER = os.path.join(BASE_DIR, "robots_template")

# register above folder as a template-dir
TEMPLATES[0]["DIRS"] += [ROBOTS_TXT_FOLDER, ]


APIS_IMPORT_PROJECT_IIIF_BASE_URL = "https://iiif.acdh-dev.oeaw.ac.at/iiif/images/viecpro/"


# Bibsonomy Settings
APIS_BIBSONOMY = [{
    'type': 'zotero',  # or zotero
    'url': 'https://api.zotero.org/',  # url of the bibsonomy instance or zotero.org
    # for zotero use the user id number found in settings
    'user': os.getenv("ZOTERO_USER"),
    'API key': os.getenv("ZOTERO_API_KEY"),
    'group':  os.getenv("ZOTERO_GROUP"),
}]

DJANGO_TYPESENSE = {
    "collection_prefix": "viecpro_",
}


MIDDLEWARE += [
]
