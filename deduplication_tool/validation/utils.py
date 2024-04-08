from deduplication_tool.validation.datastructures import *

def get_selection_state_from_dict(data:RawSelectionState):
    groups: list[SelectionGroup] = []
    for k, v in data["groups"].items(): 
        groups.append(SelectionGroup(group_id=int(k), members=[SelectionMember(person_id=el) for el in v]))

    return SelectionState(groups=groups, singles=[SelectionSingle(person_id=el) for el in data["singles"]])



# if __name__ == "__main__": 
#     test_state:RawSelectionState = {
#         'groups': {
#             '9': [], 
#             '18': [], 
#             '3335': [79748, 75837], 
#             '3336': [], 
#             '3337': [], 
#             '6760': [], 
#             '6771': [], 
#             '6772': []
#             },
#         'singles': []
#         }
    
#     converted = get_selection_state_from_dict(test_state)

    