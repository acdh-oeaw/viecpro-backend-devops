from .models import DataSource, DataSourcePage, ImportProject
import logging

# NOTE: log level is set in .logger.py. Set level to INFO for stdout-logstreams
log = logging.getLogger("mylogger")


def create_datasource_and_pages(request):
    """
    Runs after creating a new DataSource. Initialises the DataSourcePage-objects for this DataSource.
    """
    d = {key: request.POST.get(key) for key in request.POST.keys() if key in [f.name for f in DataSource._meta.fields]}
    d["owner"] = request.user
    ds = DataSource.objects.create(**d)
    page_count = ds.page_count

    for i in range(1, int(page_count) + 1):
        page_obj, c = DataSourcePage.objects.get_or_create(DataSource=ds, page_index=i, page_token=i)
        page_obj.save()

    project = ImportProject.objects.get(pk=int(request.session.get("project_pk")))
    project.DataSources.add(ds)
    project.save()

    return ds.pk


def update_datasource_and_pages(ds):
    page_count = ds.page_count
    """
    Runs after updating an existing DataSource. Re-initialises new and updates existing DataSourcePage-objects for 
    this DataSource.
    """

    for i in range(1, int(page_count) + 1):
        log.info(i)
        page_obj, c = DataSourcePage.objects.get_or_create(DataSource=ds, page_index=i)
        if not page_obj.page_token:
            page_obj.page_token = i
        page_obj.save()

    log.info("UPDATED PAGES")
