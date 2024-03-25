import { JSXElement } from "solid-js";


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
  

type SelectionStore = {
    display: {
      groups: DisplayedGroupItem[];
      singles: DisplayedSingleItem[];
    };

    editSelection: {
      // groups: key is group id, values are selected member-ids for this group
      groups: {[key: number]: number[]};
      singles: number[];
    };
  };

interface PersonProxyResponse {
  status: string;
  person: PersonResponse;
}

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

type Group = {
  id: number;
  name: string;
  vorfin: PersonResponse;
  members: PersonProxyResponse[];
};


export type {SelectionStore, Group, SingleListItem, GroupListItem, DisplayedGroupItem, DisplayedSingleItem, PersonProxyResponse, PersonInstitutionRelation}


