from typing import Callable, Any



def process_detail_collection(processing_func: Callable, client:Any, send:bool=False):
    detail_data = processing_func()
    detail_schema = detail_data["schema"]
    detail_docs = detail_data["results"]
    collection_name = detail_schema["name"]
    print("STARTED processing detail: ", collection_name)

    try: 
        client.collections[collection_name].delete()
    except Exception as e: 
        pass

    if send: 
        client.collections.create(detail_schema)
        client.collections[collection_name].documents.import_(
            detail_docs, {"action": "create"}
        )


    print("FINISHED processing detail: ", collection_name)
