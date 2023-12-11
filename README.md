# VieCPro Backend Devops

Deployment and development repository for the VieCPro APIS instance.

This repository is forked from apis-core ("vanilla"), as apis-core is no longer in active development and adaptions to the core code where needed for VieCPro. It also adds VieCPro spefic apps directly to the repository, as these are not used in any other apps and don't need their own repositories any longer.

--> This repository is therefore no longer in sync with apis-core vanilla.

## VieCPro specific apps

VieCPro specific django-apps are added in the root directory, separate from apis_core and its nested apps.

### Table names vs. app names:

For compatibility with prior versions of this repository, where some apps had different names, all table-names of VieCPro specific apps are hardcoded
in all confliciting models via the 'meta.db_table' attribute; i.e. django app names and the prefix of the table names in your database do not exactly match. The mapping is as follows:

- `viecpro_import` == `apis_import_project`
- `viecpro_deduplication` == `dubletten_tool`

So the db-table for f.e. `viecpro_deduplication.models.group` is named `dubletten_tool_group` not `viecpro_deduplication_group`.

See the [Table Names](https://docs.djangoproject.com/en/4.2/ref/models/options/#table-names) - section of the django docs on how django handles model names and table names.

## Development Container

The devcontainer consists of the following services:

- app (the django application)
- db - a mariadb instance
- celery - a celery instance for running otherwise blocking tasks in separate workers
- typesense - a typesense server instance for testing purposes of the typesense collections build for the nuxt-frontend of the project

### Environment Variables

- for a list of environment variables needed to run this container locally, see the `env_file_template.env` file in the `.devcontainer` directory.
- set these in a file named 'devcontainer.env' within the `.devcontainer` directory

### Makefile

The Makefile contains shortcuts to commands that are frequently used in development. They can be invoked via
`make {command_name}`. See the Makfile for the full list of commands.

Note:  
A celery worker needs to be running for the application to function, you can start a new worker by running `make worker`
in the terminal.
