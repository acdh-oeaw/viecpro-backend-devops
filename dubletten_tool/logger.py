import logging
from .models import DublettenLOG
from datetime import datetime

class DatabaseHandler(logging.Handler):
    """
    Custom Handler that receives logging records and writes it to the Database. 

    Context information for the 'user' and 'action' fields is added in the log argument "extra" which expects a dictionary.
    This context information is added to the records '__dict__' object, and can be accessed by the keys given in the "extra" argument 
    provided in the call to log.info, etc. 
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    
    def emit(self, record):
        user = record.__dict__.get("user")
        action = record.__dict__.get("action")
        message = self.format(record)
        DublettenLOG.objects.create(msg=message, user=user, action=action)


def init_logger():
    LOG = logging.getLogger("DBLogger")
    #format = logging.Formatter("<<<<< LOGGER >>>>> %(module)s >>> %(funcName)s line:%(lineno)d >>> %(message)s")
    db_format = logging.Formatter("%(user)s >>> %(action)s >>> %(funcName)s >>> %(message)s")
    #handler = logging.StreamHandler()
    #file = logging.FileHandler()
    #handler.setFormatter(format)
    handlerDB = DatabaseHandler()
    handlerDB.setFormatter(db_format)
    LOG.addHandler(handlerDB)
    #LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)



