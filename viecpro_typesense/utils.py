from typing import Callable, Any
import datetime
import time


def process_detail_collection(
    processing_func: Callable[..., Any],
    client: Any,
    send: bool = False,
    col_name: str = "",
):

    print(f"STARTED processing {col_name} - detail collection")

    detail_data = processing_func()
    detail_schema = detail_data["schema"]
    detail_docs = detail_data["results"]
    collection_name = detail_schema["name"]

    try:
        client.collections[collection_name].delete()
        print(f"DELETED existing schema and index for viecpro_detail_{col_name}")
    except Exception as e:
        print(e)
        pass

    if send:
        client.collections.create(detail_schema)
        print(f"CREATED new schema viecpro_detail_{col_name}")

        client.collections[collection_name].documents.import_(
            detail_docs, {"action": "create"}
        )
        print(f"UPDATING index now ...")

    print("FINISHED processing detail: ", collection_name)


def resolve_model_instance_to_detail_collection_model(inst: Any):
    # Cases:
    # - Person (Person oder Owner)
    # - Institution (Institution, Court)
    pass


def resolve_datetime_to_timestamp(date: datetime.date):
    return int(time.mktime(date.timetuple()))
