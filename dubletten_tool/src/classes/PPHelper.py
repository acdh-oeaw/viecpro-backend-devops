from . import defaultdict, ErrorLoggerMixin

class PPHelper(ErrorLoggerMixin):
    """
    Helper class for PPKind logic. 
    Split into two classes as I need static fields on PPKind, which enums don't support. 
    Fields are added to PPHelper after PPkind is created.
    
    method: get_expectation. Takes the classification of a relation and returns the 
    expected output classification to check against.
    """
    
    errors = defaultdict(list)
    enum_errors = defaultdict(list)
    _expectation = {}
    
    @classmethod
    def get_expectation(cls, kind):
        res = cls._expectation.get(kind.name, None)
        
        if res:
            return res
        else: 
            raise KeyError(f"kind: {kind} not found in dict.keys: {cls._expectation.keys()}")
            #return []
    
   