import typesense
import os

local_client = typesense.Client(
    {
        "nodes": [
            {
                "host": "ts",  
                "port": "8108",  
                "protocol": "http", 
            }
        ],
        "api_key": "xyz",
        "connection_timeout_seconds": 350,
    }
)

remote_client = typesense.Client({
    'nodes': [{
        'host': os.getenv("REMOTE_TYPESENSE_HOST"),
        'port': os.getenv("REMOTE_TYPESENSE_PORT"),
        'protocol': 'https'
    }],
    'api_key': os.getenv("REMOTE_TYPESENSE_API_KEY"),
    'connection_timeout_seconds': 350
})
