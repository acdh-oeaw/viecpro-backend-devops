from . import defaultdict, Counter, log

class ProcessingTracker:
    """
    Helper class to 'track' PP - relations before and after writing them to the 'Vorfinale Einträge'.
    
    Differentiates in all method params between a param:'rel' - a PP - relation given in a dublette or in which
    a dublette participates and a param:'res' a relation, created from a 'rel'.
    """
    
    _data = defaultdict(set)
    _handling_counter = {}
    _result_counter = {}
    _data_key_kind_dict = {}
    group_rel_kind_counter = Counter() # unused at the moment
    
    @classmethod
    def track(cls, rel, rel_kind):
        """
        Method to track which relations where created from initial relations. I.e. PP-relations that 
        a dublette participates in. 
        Tracks how often the same relation is accessed in the code (handling_counter) and 
        creates the initial _data - dictionary, whith key: initial rel, value: list of relations created 
        from this realtion. 
        """
        if cls._data.get(rel, None):
            cls._handling_counter[rel] += 1
            #log(f"incremented handling counter to {cls._handling_counter[rel]}")

        else: 
            cls._data_key_kind_dict[rel] = rel_kind
            cls._handling_counter[rel] = 0 
            #log(f"set handling counter to 0")

    
    @classmethod
    def add(cls, rel, res, res_kind):
        """
        Method to add created relations to the different data dictionaries. 
        param: rel - initial relation and key in all dictionaries. 
        param: res - relation created from 'rel'
        param: res_kind - PPKind of created relation (res).
        """
        cls._data[rel].add((res, res_kind))
        if cls._result_counter.get(rel, None):
            cls._result_counter[rel] +=1
            #log(f"incremented result counter to {cls._result_counter[rel]}")

        else:
            #log(f"set result counter to 0")
            cls._result_counter[rel] = 0
            
    @classmethod
    def log(cls):
        """
        Method to be called after all PP-rels where written. 
        Implements checks on the stored data and logs a 
        short report of failures to the logger.
        """
        clear_flag = True

        log("\n ##### REPORT from ProcessingTracker _data")
        for k, v in cls._data.items():
            if len(v) > 1:
                clear_flag = False
                log(f"Divergent entries for rel: {k}.")
                for idx, el in enumerate(v):
                    log(f"Entry_{idx}: {el}")
        if clear_flag:
            log("Result: _data showed nothing suspicious. All good.")
        else:
            clear_flag = True
        log("\n ##### REPORT from ProcessingTracker _handling_counter")
        for k, v in cls._handling_counter.items():
            if v > 1:
                clear_flag = False
                log(f"Handling counter was '{v}' for rel: {k}.")
                log(f"Results are: ")
                for idx, el in enumerate(cls._data[k]):
                    log(f"Entry_{idx}: {el}") 
        if clear_flag:
            log("Result: _handling_counter showed nothing suspicious. All good.")
        
                    