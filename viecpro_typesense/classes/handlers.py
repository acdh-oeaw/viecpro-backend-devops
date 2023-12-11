

# TODO: removed metaclass from handler
class Handler:
    """
    """

    @classmethod
    def add_func(cls, func):
        cls.func = func
        return cls

    @classmethod
    def handle(cls, *values):
        """
        _summary_
        """

        if cls.func:
            res = cls.func(*values)
        else: 
            if len(values) > 1:
                raise Exception(f"No handler function defined, this allows for single param only, received {len(values)} instead. Params are {values}")
            else: 
                return values
        return res
    
    def __str__(self):
        return f"<{self.__class__.__name__}>"
    
    def __repr__(self):
        return self.__str__()

