from . import O
configs = {
    "field_config": {
        "attrs": 
            {
            "model": None,
            "handler": None, 
            "options": None, # Check that this does not return the same object for all configs.
            "update": "never"},
        
    }, 
    "collection_config": {
        "attrs": {
            "name":None,
            "model": None, 
            "models": [],
            #"manager":"objects", 
            #"manager_methods": ["all", "get"], 
            "name":None, 
            "update":"never", 
            "nested":False, 
            "track_model":False,
            "queryset": None,
            #"fields": [], #TODO: uncomment when implementation of parsing these fields is done
            #"exclude": [],
            },
    },

}