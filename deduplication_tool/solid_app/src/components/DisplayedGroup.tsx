import type { Component } from "solid-js";
import { useContext, For, Show } from "solid-js";
import { Group } from "../deduplication_types";
import { AppStateContext } from "../App";

const DisplayedGroup: Component<{
  group: Group;
  toggleMemberSelect: (groupId: number, memberId: number) => void;
}> = (props) => {
  const {
    selectionStore: selectionStore,
    setSelectionStore: setSelectionStore,
  } = useContext(AppStateContext);
  const group = props.group;
  const toggleMemberSelect = props.toggleMemberSelect;
  
  return (
    <>
      <div
        class="display-header"
        data-toggle="collapse"
        data-target={`#data_members_${group.id}`}
      >
        {group.name} ({group.id})
      </div>
      <div class="collapse" id={`data_members_${group.id}`}>
        <For each={group.members}>
          {(member) => (
            <>
              <div class="text-sm pt-3">
                <div class="d-flex align-items-center">
                  <Show
                    when={selectionStore.editSelection.groups[
                      group.id
                    ].includes(member.person.id)}
                  >
                    <span
                      onclick={() =>
                        toggleMemberSelect(group.id, member.person.id)
                      }
                      class="material-symbols-outlined  m-0 mr-2 my-1"
                    >
                      check_box
                    </span>
                  </Show>
                  <Show
                    when={
                      !selectionStore.editSelection.groups[
                        group.id
                      ].includes(member.person.id)
                    }
                  >
                    <span
                      onclick={() =>
                        toggleMemberSelect(group.id, member.person.id)
                      }
                      class="material-symbols-outlined m-0 mr-2 my-1"
                    >
                      check_box_outline_blank
                    </span>
                  </Show>
                  <div
                    class="person-proxy-display"
                    data-toggle="collapse"
                    data-target={`#data_proxy_relations_${member.person.id}`}
                  >
                    {member.person.name}, {member.person.first_name} (
                    {member.person.id} [{member.status}])
                  </div>
                </div>
              </div>
              <div
                class="collapse relation-display-container"
                id={`data_proxy_relations_${member.person.id}`}
              >
                <For each={member.relations}>
                  {(rel) => (
                    <>
                      <div class="relation-display-item">
                        {rel.relation_type.name}{" "}
                        {rel.related_institution.name}
                        {rel.start_date} {rel.end_date}
                      </div>
                    </>
                  )}
                </For>
              </div>
            </>
          )}
        </For>
      </div>
    </>
  );
};

export { DisplayedGroup };
