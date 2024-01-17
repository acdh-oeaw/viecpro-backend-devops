from viecpro_typesense import Schema, CollectionAdapter
from .clients import local_client, remote_client
from .collections import create_entity_collections, create_relation_collections, ReferenceCollection, HofstaatCollection
from .handlers import ErrorCount
from datetime import date
import os
from pathlib import Path
from viecpro_typesense_detail.details.detail_person import main as person_detail_main
from viecpro_typesense_detail.details.detail_institution import main as institution_detail_main
from viecpro_typesense_detail.details.detail_place import main as place_detail_main

def main(send=False, local=True):
    print("process starting")

    client = local_client
    if not local:
        client = remote_client

    vc = Schema(name="viecpro", client=client)

    rels = create_relation_collections()
    ents = create_entity_collections()
    col_relations = CollectionAdapter(name="viecpro_relations", nested=True)

    for col in rels:
        print(f"adding collection {col=} to col_relations.")
        col_relations.add_collection(col)

    for field in col_relations.collections[0].fields:
        print(f"adding field {field=} to col_relations collection")
        col_relations.add_field(field)

    for col in ents:
        vc.add_collection(col)

    vc.add_collection(ReferenceCollection)
    vc.add_collection(col_relations)
    vc.add_collection(HofstaatCollection)

    # todo: make this a utility function to reuse
    def create_schema_name():
        schemata_folder = Path("typesense-schemata")
        if not os.path.exists(schemata_folder):
            os.mkdir(schemata_folder)

        curr_date = date.today()
        template = schemata_folder / \
            f"viecpro_typesense_schema_{curr_date}.json"
        idx = 0
        while os.path.exists(schemata_folder / template):
            template = schemata_folder / \
                f"viecpro_typesense_schema_{curr_date}_{idx}.json"
            idx += 1
        print(template)
        return str(template)

    vc.schema_to_file(create_schema_name())

    print("process finished")
    if send:
        vc.send_to_server()
        print("send data to server")

    ###### Handle Detail Collections #######
    person_detail_data = person_detail_main()
    person_detail_schema = person_detail_data["schema"]
    person_detail_docs = person_detail_data["results"]

    institution_detail_data = institution_detail_main()
    institution_detail_schema = institution_detail_data["schema"]
    institution_detail_docs = institution_detail_data["results"]

    place_detail_data = place_detail_main()
    place_detail_schema = place_detail_data["schema"]
    place_detail_docs = place_detail_data["results"]


    for collection_name in [person_detail_schema["name"], institution_detail_schema["name"]]:
        try:
            client.collections[collection_name].delete()
        except Exception as e:
            pass

    if send:
        client.collections.create(person_detail_schema)
        client.collections[person_detail_schema["name"]].documents.import_(
            person_detail_docs, {"action": "create"}
        )

        client.collections.create(institution_detail_schema)
        client.collections[institution_detail_schema["name"]].documents.import_(
            institution_detail_docs, {"action": "create"}
        )
        client.collections.create(place_detail_schema)
        client.collections[place_detail_schema["name"]].documents.import_(
            place_detail_docs, {"action": "create"}
        )

    return vc
