import type { Component } from "solid-js";
import { useContext, Show, For, createSignal } from "solid-js";
import { AppStateContext } from "../App";
import { PersonProxyResponse } from "../deduplication_types";

const DisplayedSingle: Component<{
  single: PersonProxyResponse;
}> = (props) => {
  const {
    selectionStore: selectionStore,
    setSelectionStore: setSelectionStore,
    toggleSingleDisplay: toggleSingleDisplay,
    toggleDisplayedSingleSelect: toggleDisplayedSingleSelect,
    getDetail: getDetail,
  } = useContext(AppStateContext);

  const single = props.single;
  const [eyeIcon, setEyeIcon] = createSignal<string>("visibility");

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
            class="person-proxy-display auto-collapsable-single-relations-container collapsed"
            data-toggle="collapse"
            data-target={`#data_proxy_relations_${single.person.id}`}
          >
            <div class="d-flex flex-inline align-items-center">
              <span
                class="material-symbols-outlined mr-2"
                style={{ cursor: "pointer" }}
                onmouseover={() => setEyeIcon("visibility_off")}
                onmouseleave={() => setEyeIcon("visibility")}
                onclick={() =>
                  toggleSingleDisplay(
                    single.person.id,
                    selectionStore.display.singles.find(
                      (el) => el.id === single.person.id
                    )!.listItem
                  )
                }
              >
                {eyeIcon()}
              </span>
              <span>
                {single.person.name}, {single.person.first_name} (
                {single.person.id} [{single.status}]){" "}
              </span>
            </div>
          </div>
          <button
            class="btn btn-sm btn-outline-none btn-icon mb-0"
            onclick={() => {
              getDetail(single.person.id);
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
