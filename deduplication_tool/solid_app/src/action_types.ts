
interface RemoveMemberState {
    group_id: number,
    old_vorfin: number,
    members_to_remove: number[]
}

interface DissolveGroupState {
    group_id: number, 
    old_vorfin: number,
    old_members: number[]
}


interface MergeSelectedMembersState{
    group_id: number, 
    old_vorfin: number,
    members_to_merge: number[]
}


interface RemergeGroupState{
    group_id: number, 
    old_vorfin: number,
}

interface MergeAllState{
    singles: number[],
    groups: number[]
    new_group_name: string
}

interface GroupSelectedState{
    singles: number[],
    groups: {[key:number]: number[]}
    new_group_name: string
}

interface CreateGroupFromSingleState{
    new_group_name: string
    single: number
}

export type { RemoveMemberState, DissolveGroupState, MergeAllState, MergeSelectedMembersState, GroupSelectedState, RemergeGroupState,CreateGroupFromSingleState}