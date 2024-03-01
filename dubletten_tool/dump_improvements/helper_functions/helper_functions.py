"""
Collect re-usable code snippets / functions in here and import them into our notebooks where needed. 

Please write a short dosctring what the function should do. Once implement, don't change the function without ensuring, that it still works in the context it was written for. 
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase
from typing import Callable
from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_relations.models import AbstractRelation
import pandas as pd



############# Functions to get list of models and list of model names #####


def get_all_relation_classes():
    return AbstractRelation.get_all_relation_classes()

def get_all_entity_classes():
    return AbstractEntity.get_all_entity_classes()

def get_all_entity_names():
    return AbstractEntity.get_all_entity_names()

def get_all_relation_names():
    return AbstractRelation.get_all_relation_names()



############ Functions to get dataframe ##########


def df_from_values(model, values=None):
    """
    Give a model and receive the dataframe constructed from model.objects.values().
    Optional: give a list of field_names, and get only those values
    """
    if not values:
        return pd.DataFrame(model.objects.values())
    else: 
        if isinstance(values, list):
            return pd.DataFrame(model.objects.values(*values))
        else:
            raise TypeError()

############# Functions intendet to be used as decorators #################



def generic_assert_instance_count_integrity(entities:bool=True, types:bool=True, relations:bool=True, relation_types:bool=True, exclude:list=None, include:list=None)->Callable:
    """
    Generic Decorator that accepts arguments to be used in functions that alter data. By default, tests instance count
     Integrity of all 
    entity, relation, type, and relationtype models before and after executing the wrapped function.
    Throws an assertion error if the instance count diverges.
    You can manage the models to be tested in the following ways:
    - on a per group basis: set the model group argument to False.
        example: (entities=False) --> excludes Person, Institution, Work, Event, Place) from the test
    - you can exclude specific models by passing them in a list in the exclude parameter
        example: (exlude=[Person]) NOTE: pass the model-class as an Object, not a string
    - you can include specific models py passing them in the include list
        example: (entities=False, include=[Person, Work]) --> excludes all entites except Person and Work


    # todo: add a return of new errenous instances on check 
    """
    
    ######### check params #######
    for p in [entities, types, relations, relation_types]:
            if not isinstance(p, bool):
                raise TypeError(f"Expected boolean argument, got {p} with type {type(p)} instead.")
    
    if exclude and not isinstance(exclude, list):
        if isinstance(exclude, ModelBase):
            exclude = [exclude]  
        else:
            raise ValueError(f"Param 'exclude' must be an empty list or a list of Model-objects, got {type(exclude)} instead.")
    
    if include and not isinstance(include, list):
        if isinstance(include, ModelBase):
            include = [include]
        else:
            raise ValueError(f"Param 'include' must be an empty list or a list of Model-objects, got {type(exclude)} instead.")
    
    ######## setup data #########
    
    # to check if group is disabled
    arg_mapping = {
        "entities":entities,
        "relations":relations,
        "relation_types":relation_types,
        "types":types
    }
    
    # mapping between the group of models and the lookup dict to be used in destructuring
    model_lookup_dict = {
        "entities": {"app_label":"apis_entities"},
        "types": {"app_label":"apis_vocabularies", "model__icontains":"type"},
        "relations": {"app_label":"apis_relations"},
        "relation_types":{"app_label":"apis_vocabularies", "model__iendswith":"relation"},
    }
    
    def get_model_set(model_lookup_dict:dict)->set:
        
        # to store the references to the model class instances (Objects)
        model_list = []
        
        # populate the model_list
        for key, kwargs in model_lookup_dict.items():

            # check if the group is disabled
            if arg_mapping[key]:
            
                # add all model classes to the model_list
                model_list += [c.model_class() for c in ContentType.objects.filter(**kwargs)]
            

        # exclude unwanted models
        if exclude:
            for ex in exclude:
                if ex in model_list:
                    model_list.remove(ex)

        # include further models or models belonging to a group that has been disabled as a whole
        if include:
            for inc in include:
                if inc not in model_list:
                    model_list.append(inc)

        # deduplicate models
        model_set = set(model_list)

       
        return model_set
    
    model_set = get_model_set(model_lookup_dict)
    
     # setup the model dict that stores the values from before and after the func executes
    count_dict = {m:{"before":-10, "after":-10} for m in model_set}
    
    
    ###### wraper logic ########
    
    def decorator(func:Callable)->Callable:
        def wrapper(*args, **kwargs):
            failed = False 
            err_count = 0         
            # calculate the before val for all models
            for m in count_dict.keys():
                count_dict[m]["before"] = m.objects.count()
            
            # execute the wrapped function and store the return val in res
            res = func(*args,**kwargs)
            
            # calcualte the after val for all models
            for m in count_dict.keys():
                count_dict[m]["after"] = m.objects.count()

            
            # loop through assert - the actual test
            for m, val in count_dict.items():
                before, after = val["before"], val["after"]
                try:
                    assert before == after, f"Failed integrity test for {m};\nInstanceCount diverges:\nBefore: {before}\nAfter: {after}"
                except AssertionError as e:
                    failed=True
                    err_count += 1
                    print(e)
            print(f"Report from generic_assert_instance_count_integrity: tested: {[m.__name__ for m in model_set]}")
            if not failed:
                print("Report from generic_assert_instance_count_integrity: All integrity tests passed.")
            else: 
                print(f"Report from generic_assert_instance_count_integrity: Failed with {err_count} - Errors. Complete report: {count_dict}")
            return res
        return wrapper
    return decorator
    
    

def generic_count_test(test_func=None, model=None):
    """
    Decorator function with arguments to test if a function removes objects in some models.
    Expects either a test_func, that returns the count of objects, like:
    test_func = lambda : len(PersonInstitution.objects.all())
    or a model to construct the test function from.
    """

    # check if both arguments are None and raise error in this case
    if test_func == model == None:
        raise ValueError("Both optional arguments are None, you must either pass in a test_func or a model-object")
    elif test_func == None:
        test_func = lambda: model.objects.count()

    def decorator(func):
        def wrapper(*args, **kwargs):
            # check count before calling decorated function
            value_before = test_func()
            res = func(*args, **kwargs)
            # check count after calling decorated functin
            value_after = test_func()

            # assert nothing was changed
            assert value_before == value_after, f"Count test for {model}, should be the same {value_before} == {value_after}"
            print("test returned:", value_before, value_after)
            return res

        return wrapper

    return decorator


def generic_duplicates_test(model):
    """
    Test if a model has duplicates before and after running a processing function.
    """
    def no_duplicates():
        objects = model.objects.all()
        names = [o.name for o in objects]
        if len(set(names)) == len(names):
            return True
        else:
            return False

    def decorator(func):
        def wrapper(*args, **kwargs):
            assert no_duplicates()
            res = func(*args, **kwargs)
            assert no_duplicates(), f"Duplicate Test for model: {model} should be True (no duplicates), test was {no_duplicates()}"
            return res
        return wrapper
    return decorator




def generic_count_test_all_models():
    rel_models = ContentType.objects.filter(app_name="apis_relations")