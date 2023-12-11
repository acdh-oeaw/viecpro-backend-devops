import json
from jinja2 import Environment, FileSystemLoader


class Schema:
    def __init__(self, name, client, collections=[], *args, **kwargs):
        self.name = name
        self._collections = collections
        self.client = client

    @property
    def collections(self):
        return self._collections

    @collections.setter
    def collections(self, cols):
        assert isinstance(cols, (list, set, tuple))
        self._collections = cols

    def add_collection(self, col):
        if col in self._collections:
            self._collections.remove(col)
            self._collections.append(col)
        else:
            self._collections.append(col)

    def remove_collection(self, col):
        if col in self._collections:
            self._collections.remove(col)

    def get_schema(self):
        schema = {}
        for col in self._collections:
            if "CollectionAdapter" not in [col.__class__.__name__]:
                schema.update({col.config.name: col.schema()})
            else:
                schema.update({col.name: col.schema()})
        for k in schema.keys():
            print(k)

        return schema

    def get_documents(self):
        res = {}
        for c in self._collections:
            print(c)
            if "CollectionAdapter" not in [c.__class__.__name__]:
                res.update({c.config.name: c._get_docs()})
            else:
                res.update({c.name: c._get_docs()})

        return res

    def docs_to_file(self, filename):
        docs = self.get_documents()

        with open(filename, "w") as file:
            data = json.dumps(docs)
            file.write(data)

    def schema_to_file(self, filepath: str):
        print(f"{filepath=}")
        if filepath.endswith(".json"):
            with open(filepath, "w") as file:
                data = json.dumps(self.get_schema())
                file.write(data)

        elif filepath.endswith(".py"):
            with open(filepath, mode="w", encoding="utf-8") as file:
                environment = Environment(
                    loader=FileSystemLoader("django_typesense/jinja_templates/")
                )
                template = environment.get_template("schema_with_collections.jinja")

                content = template.render(schema=self)
                file.write(content)
        else:
            raise ValueError(
                f"Expected filepath to end either with '.json' or '.py', received '{filepath}' - instead."
            )

    def send_to_server(self):
        client = self.client
        for c in self.collections:
            schema = c.schema()

            if not schema["name"].startswith("viecpro_"):
                schema["name"] = "viecpro_" + schema["name"]
            try:
                client.collections[schema["name"]].delete()
                print(f"sending: deleted-schema: {schema['name']}")
            except:
                print("raised pass error")
                pass

            client.collections.create(schema)
            print(f"sending: created-schema: {schema['name']}")

            try: 
                if "CollectionAdapter" not in [c.__class__.__name__]:
                    # TODO: refactor this temporarily workaround once collection Adapter is a stable class
                    # TODO: remove this wrapper that breaks the normal manager!
                    docs = c._get_docs()
                else:
                    # if collection is collection adapter, call _get_docs directly
                    print("called get docs for collection adapter")
                    docs = c._get_docs()
                    print("finished creating docs, num docs is:", len(docs))

                client.collections[schema["name"]].documents.import_(
                    docs, {"action": "create"}
                )
            except Exception as e: 
                print("error in: ", schema["name"], e)
                continue

    #  self.delete_collection("entities")

    #     try:
    #         self.client.collections[name].delete()
    #     except Exception as e:
    #         print(f"Caught exception {e}")

    #     schema = entities
    #     label_fields = LABEL_FIELDS
    #     print(f"Label-Fields: {label_fields}")
    #     schema_fields = [f["name"] for f in schema["fields"] if not f["name"] in label_fields]

    #     client.collections.create(schema)

    #                 client.collections["entities"].documents.create(values)
