import type { Component, JSXElemen } from "solid-js";
import styles from "./App.module.css";
import $ from "jquery";
import {
  createSignal,
  For,
  createMemo,
  createResource,
  createEffect,
  Show,
  createContext,
} from "solid-js";
import { createStore, unwrap, produce } from "solid-js/store";
import type {
  Group,
  PersonProxyResponse,
  SingleListItem,
  DisplayedSingleItem,
  DisplayedGroupItem,
  SelectionStore,
  GroupListItem,
} from "./deduplication_types";
import { DisplayedSingle } from "./components/DisplayedSingle";
import { DisplayedGroup } from "./components/DisplayedGroup";

const API_BASE = "/deduplication_tool/api/";
let detailContent: HTMLDivElement | undefined = undefined;

function getCookie(cname: string) {
  // for passing djangos csrfToken to ajax-calls
  const name = cname + "=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}
//  main store to handle displayed (selected from browser) and selected items (selected in edit section)
const [selectionStore, setSelectionStore] =
  createStore<SelectionStore>({
    display: {
      groups: [],
      singles: [],
    },
    editSelection: {
      groups: {},
      singles: [],
    },
  });

const [singleQuery, setSingleQuery] = createSignal<string>();
const [groupQuery, setGroupQuery] = createSignal<string>();

const toggleDisplayedSingleSelect = (id: number) => {
  // handles selecting a displayed singles check-box (toggles it)
  if (selectionStore.editSelection.singles.includes(id)) {
    // remove single from editSelection
    setSelectionStore("editSelection", "singles", (prev) =>
      prev.filter((el) => el !== id)
    );
  } else {
    // add single to editSelection
    setSelectionStore(
      "editSelection",
      "singles",
      selectionStore.editSelection.singles.length,
      id
    );
  }
};
const toggleMemberSelect = (groupId: number, memberId: number) => {
  // handles selecting a displayed group-member (toggles it)
  if (
    selectionStore.editSelection.groups.filter(
      (el) => el.id === groupId
    ).length === 1 &&
    selectionStore.editSelection.groups
      .filter((el) => el.id === groupId)[0]
      .members.includes(memberId)
  ) {
    setSelectionStore(
      "editSelection",
      "groups",
      (el) => el.id === groupId,
      "members",
      (prev) => prev.filter((el) => el !== memberId)
    );
  } else {
    setSelectionStore(
      "editSelection",
      "groups",
      (el) => el.id === groupId,
      (el) => el.members.length,
      memberId
    );
  }
};

async function startAction(action: string) {
  const data = unwrap(selectionStore.editSelection);
  const serializedData = JSON.stringify(data);
  console.log(serializedData);
  const response = (
    await fetch(`/deduplication_tool/actions/${action}/`, {
      method: "POST",
      body: serializedData,
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
  )
    .json()
    .then((json) => console.log(json));
}

async function fetchSingleList(query: string) {
  // fetches the browsing-list for singles with current query
  // returns a promise to work with createResource
  const url = API_BASE + "singles-list/" + query;
  const response = await fetch(url, {
    headers: {
      Accept: "*/*",
      "Content-Type": "application/json",
    },
  });
  // why await? entweder then oder await
  return await response
    .json()
    .then((d) =>
      d.results.filter(
        (el: SingleListItem) =>
          !selectionStore.display.singles
            .map((single) => single.id)
            .includes(el.id)
      )
    );
}

async function fetchGroupList(query: string) {
  // fetches the browsing-list for groups with current query
  // returns a promise to work with createResource
  const url = API_BASE + "groups-list" + query;
  const response = await fetch(url, {
    headers: {
      Accept: "*/*",
      "Content-Type": "application/json",
    },
  });
  return await response
    .json()
    .then((d) =>
      d.results.filter(
        (el: GroupListItem) =>
          !selectionStore.display.groups
            .map((group) => group.id)
            .includes(el.id)
      )
    );
}

const [singleList, { mutate: mutateSingleList }] = createResource(
  singleQuery,
  fetchSingleList
);
const [groupList, { mutate: mutateGroupList }] = createResource(
  groupQuery,
  fetchGroupList
);

const fetchSingle = async (id: number, storeIndex: number) => {
  const url =
    API_BASE + "singles-object/?person__id=" + id.toString();
  try {
    const response = await fetch(url, {
      headers: {
        Accept: "*/*",
        "Content-Type": "application/json",
      },
    });
    await response
      .json()
      .then((response) => response.results[0])
      .then((single: PersonProxyResponse) => {
        setSelectionStore("display", "singles", storeIndex, {
          id: id,
          element: <DisplayedSingle single={single} />,
        });
      });
  } catch (err) {
    setSelectionStore("display", "singles", storeIndex, {
      id: id,
      element: <div>Failed to fetch single with id: {id}</div>,
      // TODO: check that this is shallow merged, i.e. the listItem is persisted
    });
  }
};

const fetchGroup = async (id: number, indexToInsert: number) => {
  const url = API_BASE + "groups-object/" + id.toString();
  try {
    const response = await fetch(url, {
      headers: {
        Accept: "*/*",
        "Content-Type": "application/json",
      },
    });
    await response.json().then((group: Group) =>
      setSelectionStore("display", "groups", indexToInsert, {
        id: id,
        element: <DisplayedGroup group={group} />,
      })
    );
  } catch (err) {
    setSelectionStore("display", "groups", indexToInsert, {
      id: id,
      element: <div>Failed to fetch group with id: {id}</div>,
      // TODO: check that this is shallow merged, i.e. the listItem is persisted
    });
  }
};
const toggleSingleDisplay = (id: number, item: SingleListItem) => {
  // handles complex intersection of ui state and data handling
  if (
    selectionStore.display.singles.filter((el) => el.id === id)
      .length === 1
  ) {
    // first, remove single from the displayed selection
    setSelectionStore(
      "display",
      "singles",
      (prev: DisplayedSingleItem[]) =>
        prev.filter((el) => el.id !== id)
    );
    // then remove single from edit selection if checked
    if (selectionStore.editSelection.singles.includes(id)) {
      setSelectionStore("editSelection", "singles", (prev) =>
        prev.filter((el) => el !== id)
      );
    }
    // then move the item back to the single list
    mutateSingleList((prev) => [item, ...prev]);
  } else {
    // add the single to the displayed singles
    const indexToInsert = selectionStore.display.singles.length;
    setSelectionStore("display", "singles", indexToInsert, {
      id: id,
      element: <div>Loading (from setAppStore)</div>,
      listItem: item,
    });
    // remove the item from the singleList
    mutateSingleList((prev: SingleListItem[]) =>
      prev.filter((el) => el.id !== item.id)
    );
    // fetch the full single data
    fetchSingle(id, indexToInsert);
  }
};

const toggleGroupDisplay = (id: number, item: GroupListItem) => {
  // handles complex intersection of ui state and data handling

  if (
    selectionStore.display.groups.filter((el) => el.id === id)
      .length === 1
  ) {
    // remove the group from the selection
    setSelectionStore(
      "display",
      "groups",
      (prev: DisplayedGroupItem[]) =>
        prev.filter((el) => el.id !== id)
    );
    // remove the group from the edit selection
    setSelectionStore(
      "editSelection",
      "groups",
      produce((prev) => prev.filter((el) => el.id !== id))
    );
    // (prev) => {
    //prev.filter((el) => el.id !== id)

    //   console.log("previous", prev);
    //   const { [id]: groupToRemove, ...remaining } = prev;
    //   console.log("remaining groups", remaining);
    //   console.log("group to remove:", groupToRemove);
    //   return remaining;
    // });
    // add the group-list-item back to the groupList
    mutateGroupList((prev) => [item, ...prev]);
  } else {
    // add the group to the selection
    const indexToInsert = selectionStore.display.groups.length;
    setSelectionStore("display", "groups", indexToInsert, {
      id: id,
      element: <div>Loading (from setAppStore)</div>,
      listItem: item,
    });
    // set the edit selection for the group and set the selectedMembers array to empty
    setSelectionStore("editSelection", "groups", id, []);
    // remove the group-llist-item from groupList
    mutateGroupList((prev: GroupListItem[]) =>
      prev.filter((el) => el.id !== item.id)
    );
    // fetch the full group data
    fetchGroup(id, indexToInsert);
  }
};

async function getDetail(perId: number) {
  const result_html = fetch(
    `/dubletten/get_person_detail/${perId.toString()}/`
  )
    .then((response) => response.json())
    .then((json) => {
      // yeah, that is strange, but I need to use jquery for the ampel to work correctly.
      $("#detail_section").html(json.html);
    });
}

export const AppStateContext = createContext({
  selectionStore,
  setSelectionStore,
  toggleSingleDisplay,
  toggleGroupDisplay,
  toggleMemberSelect,
  mutateSingleList,
  mutateGroupList,
  fetchGroup,
  fetchSingle,
  toggleDisplayedSingleSelect,
  getDetail,
  getCookie,
  startAction,
});

const App: Component = () => {
  // refs
  let searchInput: HTMLInputElement | undefined = undefined;
  let searchModeSelect: HTMLSelectElement | undefined = undefined;

  // designates if search string should search for singles, groups or both
  const [searchMode, setSearchMode] = createSignal<string>("both");

  // signals to be provided to createResource (for browser view singles and group lists)

  createEffect(() => {
    switch (searchMode()) {
      case "both":
        searchInput!.placeholder = "search for groups and singles";
        break;
      case "singles":
        searchInput!.placeholder = "search for singles";
        break;

      case "groups":
        searchInput!.placeholder = "search for groups";
        break;
    }
  });
  const resetStore = () => {
    // clears all selections
    // TODO: consider iterating through the displayed singles and groups and moving listItems back to browser-lists
    setSelectionStore("display", "groups", []);
    setSelectionStore("display", "singles", []);
    setSelectionStore("editSelection", "groups", {});
    setSelectionStore("editSelection", "singles", []);
  };

  const singlesCount = createMemo(() => singleList()?.length);
  const groupsCount = createMemo(() => groupList()?.length);
  const displayedSinglesCount = createMemo(
    () => selectionStore.display.singles.length
  );

  const displayedGroupsCount = createMemo(
    () => selectionStore.display.groups.length
  );

  async function searchItems() {
    // over complex search function that creates the query string for search
    const searchValue =
      searchInput && searchInput.value
        ? `search=${searchInput.value}`
        : null;
    const genderNode: HTMLInputElement | null =
      document.querySelector(
        "input[name='gender-radio-group']:checked"
      );
    const genderValue =
      genderNode && genderNode.value
        ? `_gender=${genderNode.value}`
        : null;
    let queryString: string = "";

    if (genderValue && searchValue) {
      queryString = `?${genderValue}&${searchValue}`;
    } else if (genderValue) {
      queryString = `?${genderValue}`;
    } else if (searchValue) {
      queryString = `?${searchValue}`;
    } else {
      console.log("both gender and search value where none");
    }
    // check which lists should be fetched and dispatch the query
    switch (searchMode()) {
      case "both":
        setSingleQuery(queryString);
        setGroupQuery(queryString);
        break;
      case "singles":
        setSingleQuery(queryString);
        break;
      case "groups":
        setGroupQuery(queryString);
        break;
    }
  }

  function expandAll() {
    // should expand all collapes member containers of groups and all relation containers of each member and single
    // targets:
    // auto-collapsable-group-container
    // auto-collapsable-member-relations-container
    // auto-collapsable-single-relations-container
    // debug: to work, the element must have the collapsed class attached if it is collapsed at start of the app.

    document
      .querySelectorAll(
        ".auto-collapsable-group-container, .auto-collapsable-member-relations-container, .auto-collapsable-single-relations-container"
      )
      .forEach((el) => {
        if (el.classList.contains("collapsed")) {
          // @ts-ignore
          el.click();
        }
      });
  }

  function collapseAll() {
    // exact reverse of expandAll()
    document
      .querySelectorAll(
        ".auto-collapsable-group-container, .auto-collapsable-member-relations-container, .auto-collapsable-single-relations-container"
      )
      .forEach((el) => {
        if (!el.classList.contains("collapsed")) {
          // @ts-ignore
          el.click();
        }
      });
  }
  return (
    <AppStateContext.Provider
      value={{
        selectionStore: selectionStore,
        setSelectionStore: setSelectionStore,
        toggleGroupDisplay: toggleGroupDisplay,
        toggleMemberSelect: toggleMemberSelect,
        toggleSingleDisplay: toggleDisplayedSingleSelect,
        toggleDisplayedSingleSelect: toggleDisplayedSingleSelect,
        fetchGroup: fetchGroup,
        fetchSingle: fetchSingle,
        mutateGroupList: mutateGroupList,
        mutateSingleList: mutateSingleList,
        getDetail: getDetail,
        getCookie: getCookie,
        startAction: startAction,
      }}
    >
      <div class="container-fluid w-100 d-flex">
        {/* --- Start Browser Section */}
        <div class="col pt-5 pb-3">
          <button
            class="btn btn-danger mb-4"
            onclick={() => resetStore()}
          >
            Reset Store
          </button>
          <div class="container-fluid border border-secondary rounded py-4 px-2 mb-4">
            <div class="input-group mb-3">
              <select
                class="form-select btn-secondary text-sm rounded-left "
                aria-label="Example select with button addon"
                ref={searchModeSelect}
                onchange={() =>
                  setSearchMode(searchModeSelect!.value)
                }
              >
                <option value="both" selected>
                  Both
                </option>
                <option value="singles">Singles</option>
                <option value="groups">Groups</option>
              </select>
              <input
                class="form-control form-control-sm"
                type="search"
                placeholder="search for groups and singles"
                id="search-input"
                ref={searchInput}
                onkeydown={(event) => {
                  if (event.key === "Enter") {
                    event.stopPropagation();
                    event.preventDefault();
                    searchItems();
                  }
                }}
              />

              <button
                type="button"
                class="btn btn-primary m-0 btn-sm rounded-right"
                onclick={searchItems}
              >
                Search
              </button>
            </div>

            <div class="d-flex" style={"font-size: .8rem;"}>
              <span class="mr-4">Gender:</span>
              <div class="form-check form-check-inline mx-1">
                <input
                  checked
                  class="form-check-input"
                  type="radio"
                  name="gender-radio-group"
                  id="gender-choice-male"
                  value="male"
                />
                <label
                  class="form-check-label mr-2"
                  for="gender-choice-male"
                >
                  Male
                </label>
              </div>
              <div class="form-check form-check-inline mx-1">
                <input
                  class="form-check-input"
                  type="radio"
                  name="gender-radio-group"
                  id="gender-choice-female"
                  value="female"
                />
                <label
                  class="form-check-label mr-2"
                  for="gender-choice-female"
                >
                  Female
                </label>
              </div>
              <div class="form-check form-check-inline mx-1">
                <input
                  class="form-check-input"
                  type="radio"
                  name="gender-radio-group"
                  id="gender-choice-other"
                  value="third gender"
                />
                <label
                  class="form-check-label mr-2"
                  for="gender-choice-other"
                >
                  Other/None
                </label>
              </div>
            </div>
          </div>
          <div id="menu_navigation">
            <ul class="nav nav-tabs" id="myTab" role="tablist">
              <li class="nav-item" role="presentation">
                <a
                  class="nav-link active"
                  id="groups-tab"
                  data-toggle="tab"
                  href="#groups_section"
                  role="tab"
                >
                  Groups
                  <span
                    class="badge badge-pill ml-2"
                    style={{
                      "background-color":
                        displayedGroupsCount() > 0
                          ? "lightblue"
                          : "lightgray",
                    }}
                  >
                    {displayedGroupsCount()}
                  </span>
                  <span
                    class="badge badge-pill ml-1"
                    style={{
                      "background-color":
                        groupsCount() > 0 ? "#0d6efd" : "lightgray",
                      color: groupsCount() > 0 ? "white" : "black",
                    }}
                  >
                    {groupsCount()}
                  </span>
                </a>
              </li>
              <li class="nav-item" role="presentation">
                <a
                  class="nav-link"
                  id="singles-tab"
                  data-toggle="tab"
                  href="#singles_section"
                  role="tab"
                >
                  Singles
                  <span
                    class="badge badge-pill ml-2"
                    style={{
                      "background-color":
                        displayedSinglesCount() > 0
                          ? "lightblue"
                          : "lightgray",
                    }}
                  >
                    {displayedSinglesCount()}
                  </span>
                  <span
                    class="badge badge-pill ml-1"
                    id="group_count_badge_{{g.id}}"
                    style={{
                      "background-color":
                        singlesCount() > 0 ? "#0d6efd" : "lightgray",
                      color: singlesCount() > 0 ? "white" : "black",
                    }}
                  >
                    {singlesCount()}
                  </span>
                </a>
              </li>
            </ul>
          </div>
          <div class="" id="browser_content">
            <div class="tab-content" id="myTabContent">
              <div
                class="tab-pane show active"
                id="groups_section"
                role="tabpanel"
              >
                <div
                  class="container-fluid mt-4"
                  style="overflow-y: scroll; height: 80vh"
                >
                  <ul class="m-0 pl-0 list-group mb-4">
                    <For
                      each={selectionStore.display.groups.map(
                        (group) => group.listItem
                      )}
                    >
                      {(item) => (
                        <>
                          <li
                            class="list-group-item m-o d-flex justify-content-between align-items-center "
                            onclick={() =>
                              toggleGroupDisplay(item.id, item)
                            }
                            style={{
                              "background-color": "lightblue",
                            }}
                          >
                            {item.name} ({item.id}){" "}
                            <span class="badge badge-primary badge-pill">
                              {item.count}
                            </span>
                          </li>
                        </>
                      )}
                    </For>
                  </ul>
                  <ul class="m-0 pl-0 list-group">
                    <For
                      each={groupList()}
                      fallback={<div>No Results</div>}
                    >
                      {(item) => (
                        <>
                          <li
                            class="list-group-item m-o d-flex justify-content-between align-items-center "
                            onclick={() =>
                              toggleGroupDisplay(item.id, item)
                            }
                            style={{
                              "background-color": "white",
                            }}
                          >
                            {item.name} ({item.id}){" "}
                            <span class="badge badge-primary badge-pill">
                              {item.count}
                            </span>
                          </li>
                        </>
                      )}
                    </For>
                  </ul>
                </div>
              </div>
              <div
                class="tab-pane"
                id="singles_section"
                role="tabpanel"
              >
                <div
                  class="container-fluid mt-4"
                  style="overflow-y: scroll; height: 80vh"
                >
                  <ul class="m-0 pl-0 list-group mb-4">
                    <For
                      each={selectionStore.display.singles.map(
                        (single) => single.listItem
                      )}
                    >
                      {(item) => (
                        <>
                          <li
                            class="list-group-item w-100 m-0"
                            onclick={() =>
                              toggleSingleDisplay(item.id, item)
                            }
                            style={{
                              "background-color": "lightblue",
                            }}
                          >
                            {item.name}, {item.first_name} ({item.id})
                          </li>
                        </>
                      )}
                    </For>
                  </ul>
                  <ul class="m-0 pl-0 list-group">
                    <For
                      each={singleList()}
                      fallback={<div>No Results</div>}
                    >
                      {(item) => (
                        <>
                          <li
                            class="list-group-item w-100 m-0"
                            onclick={() =>
                              toggleSingleDisplay(item.id, item)
                            }
                            style={{
                              "background-color": "white",
                            }}
                          >
                            {item.name}, {item.first_name} ({item.id})
                          </li>
                        </>
                      )}
                    </For>
                  </ul>
                </div>
              </div>
              <div
                class="tab-pane fade"
                id="marked_section"
                role="tabpanel"
              >
                Not implemented yet
              </div>
            </div>
          </div>
        </div>
        {/* --- End Browser Section */}
        {/* --- Start Display Section */}

        <div class="container-fluid pt-5 pb-3">
          <div class="d-flex flex-inline justify-content-center align-items-center">
            <button
              class="btn btn-outline-none btn-icon"
              onclick={() => expandAll()}
            >
              <span class="material-symbols-outlined">
                expand_all
              </span>
            </button>
            <button
              class="btn btn-outline-none btn-icon"
              onclick={() => collapseAll()}
            >
              <span class="material-symbols-outlined">
                collapse_all
              </span>
            </button>
            <h4 class="pl-0 mr-4">Selected</h4>

            <div class="dropdown">
              <button
                class="btn btn-sm btn-outline-secondary btn-icon dropdown-toggle"
                type="button"
                id="selection-action-dropdown"
                data-toggle="dropdown"
                aria-expanded="false"
              >
                <span class="material-symbols-outlined">
                  settings
                </span>
              </button>
              <div class="dropdown-menu">
                <li
                  class="dropdown-item"
                  onclick={() => startAction("merge_all")}
                >
                  {/* this should only show if more than one group or single are displayed */}
                  <span> merge all</span>
                </li>
                <li
                  class="dropdown-item"
                  onclick={() => startAction("group_selection")}
                >
                  {/* this should only show if more than one single or member are selected */}
                  <span> group selected </span>
                </li>
                <li class="dropdown-item">
                  <span onclick={resetStore}>clear display</span>
                </li>
              </div>
            </div>
          </div>
          <div
            class="pl-2 pb-5"
            id="relations-section"
            style="overflow-y: scroll; height: 120vh;"
          >
            <Show when={selectionStore.display.groups.length > 0}>
              <div class="m-0 p-0">
                <For
                  each={selectionStore.display.groups.map(
                    (el) => el.element
                  )}
                  fallback={<div>No groups selected</div>}
                >
                  {(item) => item}
                </For>
              </div>
            </Show>

            <Show when={selectionStore.display.singles.length > 0}>
              <div class="m-0 p-0">
                <p class="display-header">Singles</p>
                <For
                  each={selectionStore.display.singles.map(
                    (el) => el.element
                  )}
                  fallback={<div>No singles selected</div>}
                >
                  {(item) => item}
                </For>
              </div>
            </Show>
          </div>
        </div>
        {/* --- End Display Section */}
        {/* --- Start Detail Section */}

        <div class="col">
          <div class="pl-0">
            <span class="d-flex">
              <h2 class="pl-4">Detail / Suggestions</h2>
              <button
                class="btn btn-sm btn-outline-secondary ml-4"
                //onclick="clearSuggestions()"
                id="clearSuggestions"
              >
                Clear
              </button>
            </span>
          </div>

          <div
            class="pl-4 pb-5"
            ref={detailContent}
            style="width: 100%; overflow-y: scroll; height: 80vh"
            id="detail_section"
          ></div>
        </div>
        {/* --- End Detail Section */}
      </div>
    </AppStateContext.Provider>
  );
};

export default App;
