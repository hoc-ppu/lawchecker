/// <reference types="vite-plugin-svgr/client" />
import React, {
  useReducer,
  useEffect,
  Dispatch,
  SetStateAction,
  useState,
} from "react";
import UkParliamentSvg from "./../assets/ukParliament.svg?react";

import SidebarSubItem from "./SidebarSubItem";
import { PageActiveState } from "./App";

interface SidebarState {
  [key: string]: boolean; // Index signature
  menuDropdownOP: boolean;
  menuDropdownEDM: boolean;
  menuDropdownVnP: boolean;
  menuDropdownFDO: boolean;
  menuDropdownQT: boolean;
}

// Define the initial state
const initialState: SidebarState = {
  menuDropdownOP: false,
  menuDropdownEDM: false,
  menuDropdownVnP: false,
  menuDropdownFDO: false,
  menuDropdownQT: false,
};
export interface MenuItem {
  title: string;
  menuItemControles: string;
}

// const opInnerOptions: Array<MenuItem> = [
//   { title: "Get XML", menuItemControles: "opGetXmlPage" },
//   { title: "Transform HTML", menuItemControles: "opTransformHtmlPage" },
// ];

// const vnpInnerOptions: Array<MenuItem> = [
//   { title: "Get XML", menuItemControles: "opGetXmlPage" },
//   { title: "Transform HTML", menuItemControles: "opTransformHtmlPage" },
// ];

// const edmInnerOptions: Array<MenuItem> = vnpInnerOptions;

// const fdoInnerOptions: Array<MenuItem> = vnpInnerOptions;

// const qtInnerOptions: Array<MenuItem> = [
//   { title: "Get XML", menuItemControles: "opGetXmlPage" },
// ];

interface Action {
  type: string;
  payload: string;
}

// Define the reducer function
function reducer(state: SidebarState, action: Action) {
  // console.log("reducer", state, action);
  switch (action.type) {
    case "TOGGLE_DROPDOWN":
      return {
        ...initialState, // Reset all dropdowns to closed
        [action.payload]: !state[action.payload], // Toggle the selected dropdown
      };
    default:
      return state;
  }
}

interface SidebarProps {
  pageActiveState: PageActiveState;
  setPageActiveState: Dispatch<SetStateAction<PageActiveState>>;
}

const Sidebar: React.FC<SidebarProps> = ({
  pageActiveState,
  setPageActiveState,
  // toggleCollapsible,
}) => {
  // console.log("From Sidebar pageActiveState", pageActiveState);
  // console.log("From Sidebar setPageActiveState", setPageActiveState);

  const [state, dispatch] = useReducer(reducer, initialState);
  const [versionInfo, setVersionInfo] =
    React.useState<string>("No version info");

  // TODO: Fix this
  useEffect(() => {
    try {
      if (!window.pywebview) {
        console.warn("window.pywebview is not available");
        return;
      }
      if (!window.pywebview.state) window.pywebview.state = {};

      // Expose setVersionInfo in order to call it from Python
      window.pywebview.state.setVersionInfo = setVersionInfo;
    } catch (error) {
      console.error("Unable to attach setVersionInfo", error);
    }
    return;
  }, []);

  const toggleDropdown = (dropdown: string) => {
    dispatch({ type: "TOGGLE_DROPDOWN", payload: dropdown });
  };

  return (
    <div className="side-bar-top-level">
      {/* Begin Contents */}
      <div>
        <div className="figma-sidebar-navigation">
          <div className="logo-header mb-4">
            <a className="concertina" href="#app-home" role="button">
              <UkParliamentSvg />
            </a>
          </div>
          <SidebarSubItem
            title="Compare Bills"
            id="compareBillsPage"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />
          <SidebarSubItem
            title="Bill Numbering"
            id="billNumberingPage"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />
          <SidebarSubItem
            title="Check Amendment Papers"
            id="compareAmendmentsPage"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />

          <SidebarSubItem
            title="Added Names Report"
            id="addedNamesPage"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />
        </div>
      </div>

      <div className="version">
        <p>
          <small id="versionInfo">{versionInfo}</small>
        </p>
      </div>
    </div>
  );
};

export default Sidebar;
