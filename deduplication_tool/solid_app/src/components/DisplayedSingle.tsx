import type { Component } from "solid-js";
import { useContext, Show, For } from "solid-js";
import { AppStateContext } from "../App";
import { PersonProxyResponse } from "../deduplication_types";

const DisplayedSingle: Component<{
  single: PersonProxyResponse;
  toggleDisplayedSingleSelect: (id: number) => void;
}> = (props) => {
  const {
    selectionStore: selectionStore,
    setSelectionStore: setSelectionStore,
  } = useContext(AppStateContext);

  const single = props.single;
  const toggleDisplayedSingleSelect =
    props.toggleDisplayedSingleSelect;
  return (
    <>
      <div class="text-sm pt-3">
        <div class="d-flex align-items-center">
          <Show
            when={selectionStore.editSelection.singles.includes(
              single.person.id
            )}
          >
            <span
              onclick={() =>
                toggleDisplayedSingleSelect(single.person.id)
              }
              class="material-symbols-outlined  m-0 mr-2 my-1"
            >
              check_box
            </span>
          </Show>
          <Show
            when={
              !selectionStore.editSelection.singles.includes(
                single.person.id
              )
            }
          >
            <span
              onclick={() =>
                toggleDisplayedSingleSelect(single.person.id)
              }
              class="material-symbols-outlined m-0 mr-2 my-1"
            >
              check_box_outline_blank
            </span>
          </Show>
          <div
            class="person-proxy-display"
            data-toggle="collapse"
            data-target={`#data_proxy_relations_${single.person.id}`}
          >
            {single.person.name}, {single.person.first_name} (
            {single.person.id} [{single.status}])
          </div>
        </div>
      </div>
      <div
        class="collapse relation-display-container"
        id={`data_proxy_relations_${single.person.id}`}
      >
        <For each={single.relations}>
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
  );
};

export { DisplayedSingle };
