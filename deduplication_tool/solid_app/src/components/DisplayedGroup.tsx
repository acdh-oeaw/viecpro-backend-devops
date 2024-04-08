import type { Component } from "solid-js";
import { useContext, For, Show, createSignal } from "solid-js";
import { Group } from "../deduplication_types";
import { AppStateContext } from "../App";

const DisplayedGroup: Component<{
  group: Group;
}> = (props) => {
  const {
    selectionStore: selectionStore,
    setSelectionStore: setSelectionStore,
    toggleMemberSelect: toggleMemberSelect,
    toggleGroupDisplay: toggleGroupDisplay,
    startAction: startAction,
    getDetail: getDetail,
  } = useContext(AppStateContext);
  const group = props.group;
  const handleHover = () => {};
  const [eyeIcon, setEyeIcon] = createSignal<string>("visibility");
  return (
    <>
      <div class="d-flex flex-row align-items-center display-header">
        <div
          class="auto-collapsable-group-container collapsed"
          data-toggle="collapse"
          data-target={`#data_members_${group.id}`}
        >
          <div class="d-flex align-items-center">
            <span
              class="material-symbols-outlined mr-2"
              style={{ cursor: "pointer" }}
              onmouseover={() => setEyeIcon("visibility_off")}
              onmouseleave={() => setEyeIcon("visibility")}
              onclick={() =>
                toggleGroupDisplay(
                  group.id,
                  selectionStore.display.groups.find(
                    (el) => el.id === group.id
                  )!.listItem
                )
              }
            >
              {eyeIcon()}
            </span>
            <span>
              {group.name} ({group.id})
            </span>
          </div>
        </div>
        <div class="dropdown">
          <div
            class="btn-icon dropdown-toggle ml-4"
            id="selection-action-dropdown"
            data-toggle="dropdown"
            aria-expanded="false"
            style={{ cursor: "pointer" }}
          >
            <span class="material-symbols-outlined">settings</span>
          </div>
          <div class="dropdown-menu">
            {/* this should only show if more than one group or single are displayed */}
            <li
              class="dropdown-item"
              onclick={() => startAction("remerge group")}
            >
              remerge group
            </li>
            <li
              class="dropdown-item"
              onclick={() => startAction("merge_selected_members")}
            >
              merge selected members
            </li>
            <li
              class="dropdown-item"
              onclick={() => startAction("remove_selected_members")}
            >
              {/* this should only show if more than one single or member are selected */}
              <span>remove selected members </span>
            </li>
          </div>{" "}
        </div>
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
                    class="person-proxy-display auto-collapsable-member-relations-container collapsed"
                    data-toggle="collapse"
                    data-target={`#data_proxy_relations_${member.person.id}`}
                  >
                    {member.person.name}, {member.person.first_name} (
                    {member.person.id} [{member.status}])
                  </div>
                  <button
                    class="btn btn-sm btn-outline-none btn-icon mb-0"
                    onclick={() => {
                      getDetail(member.person.id);
                    }}
                  >
                    <span class="material-symbols-outlined">
                      patient_list
                    </span>
                  </button>
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
