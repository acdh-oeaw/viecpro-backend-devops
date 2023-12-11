from . import log

class ErrorLoggerMixin:
    """
    Helper class to be subclassed by all classes that process data and might throw an error.
    Logs the class, the type of error and after all processing is done, logs which 
    classes threw errors, and which passed.
    First logs an overview with the number of errors per class and errortype.
    Also logs a detailed list of all individual error messages per class and errortype.

    # todo: unsure how to reset this class, as the subclasses have each there own data dicts.
    """
    enum = None
    collected_errors = {}

    @classmethod
    def setup(cls):
        cls.enum = None
        cls.collected_errors = {}
        
    @classmethod
    def has_errors(cls):
        """
        Short helper to check if a class has errors or not.
        """
        if cls.errors.keys() or cls.enum_errors.keys():
            return True
        else:
            return False
    
    @classmethod
    def log_report(cls):
        """
        Logs if a class threw errors and if so, how many.
        """
        cls_name = cls.__name__
        has_errors = {}

        if not cls.has_errors():
            log(f"Report from {cls_name}: No Errors.")
        else: 
            log(f"{cls_name} Errors: ")
            for k, v in cls.errors.items():
                log(f"{k}: {len(v)}")
                has_errors.update({k:v})

            if cls.enum:
                log(f"{cls.enum.__name__} errors: ")
                for k, v in cls.enum_errors.items():
                    log(f"'{k}'-count: {len(v)}")
                    has_errors.update({k:v})
        
        
        if has_errors.keys():  
            cls.collected_errors.update({cls:has_errors})
 
    @classmethod               
    def log_details(cls):
        """
        Logs the individual error messages per class and errortype.
        """
        for c, errors in cls.collected_errors.items():
            for k,v in errors.items():
                log(f"Detailed Errorlog for {c} [{k}]")
                for idx, el in enumerate(v):
                    log(f"\tErr_{idx}: {el}")

        
    