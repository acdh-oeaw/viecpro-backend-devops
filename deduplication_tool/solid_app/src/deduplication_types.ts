import { JSXElement } from "solid-js";
import type {Context, Setter, Accessor} from "solid-js";
import { SetStoreFunction } from "solid-js/store";

interface PersonResponse {
    id: number;
    name: string;
    first_name: string;
    gender: string;
    start_date: string;
    end_date: string;
  }

interface PersonInstitutionRelation {
  id: number;
  start_date: string;
  end_date: string;
  relation_type: {
    id: number;
    name: string;
    name_reverse: string;
  };

  related_person: PersonResponse;

  related_institution: {
    id:number;
    name: string;
    start_date: string;
    end_date: string;
  }

}
interface PersonProxyResponse {
  status: string;
  person: PersonResponse;
  relations: PersonInstitutionRelation[];
  }


interface DisplayedGroupItem {
  id: number;
  element: JSXElement;
  listItem: GroupListItem ; 
}

interface DisplayedSingleItem {
  id: number;
  element: JSXElement;
  listItem: SingleListItem ; 
}
  
interface GroupWithMembers {
  id: number;
  members: number[];
}
interface SelectionStore{
    display: {
      groups: DisplayedGroupItem[];
      singles: DisplayedSingleItem[];
    };

    editSelection: {
      singles: number[];
    };
  };


interface GroupListItem {
  id: number;
  name: string;
  gender: string;
  count: number;
}

interface SingleListItem {
  id: number;
  name: string;
  first_name: string;
  gender: string;
  start_date: string;
  end_date: string;
}

interface Group {
  id: number;
  name: string;
  vorfin: PersonResponse;
  members: PersonProxyResponse[];
};


interface ActionDataRemoveMember {
  group_id: number;
  old_vorfin: number
  members_to_remove: number[];
}

interface ActionDataDissolveGroup {
  group_id: number;
  old_vorfin: number;
  old_members: number[]
}


interface ActionDataRemergeGroup { 
  group_id: number;
  old_vorfin: number;
}

interface ActionDataMergeAll {
  singles: number[];
  groups: {[key:number]:number[]};
  new_group_name: string;

}

interface ActionDataGroupSelected {
  singles: number[];
  groups: {[key:number]:number};
  new_group_name: string;
}

interface AppStateContextType {
  selectionStore: SelectionStore;
  setSelectionStore: SetStoreFunction<SelectionStore>;
  toggleSingleDisplay: (id:number, item:SingleListItem)=>void,
  toggleGroupDisplay: (id:number, item:GroupListItem)=>void,
  toggleMemberSelect:(event:MouseEvent, groupId: number, memberId: number) => void,
  toggleDisplayedSingleSelect:(id:number)=>void,
  mutateSingleList: Setter<any>,
  mutateGroupList: Setter<any>,
  fetchGroup: (id:number, indexToInsert:number) => Promise<void>,
  fetchSingle: (id:number, indexToInster:number)=>Promise<void>,
  getDetail: (perId:number)=>Promise<void>,
  getCookie: (cname:string)=>string,
  startAction: (action:string, targetGroup: number | undefined)=> Promise<void>,
  setGroupEditSelection: Setter<any>,
  groupEditSelection: Accessor<any>,
  
}
export type {SelectionStore, Group, SingleListItem, GroupListItem, DisplayedGroupItem, DisplayedSingleItem, PersonProxyResponse, PersonInstitutionRelation, AppStateContextType, GroupWithMembers}


