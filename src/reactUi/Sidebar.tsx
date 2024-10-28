/// <reference types="vite-plugin-svgr/client" />
import React, { useReducer } from "react";
import UkParliamentSvg from "./assets/ukParliament.svg?react";
import DocumentIcon from "./assets/documentIcon.svg?react";
import ConferenceIcon from "./assets/conferenceIcon.svg?react";
import BriefcaseIcon from "./assets/briefcaseIcon.svg?react";
import CalenderIcon from "./assets/calenderIcon.svg?react";
import SpeechBubbleIcon from "./assets/speechBubbleIcon.svg?react";
import SidebarItem from "./SidebarItem";
import SidebarSubItem from "./SidebarSubItem";

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

const opInnerOptions: Array<MenuItem> = [
  { title: "Get XML", menuItemControles: "opGetXmlPage" },
  { title: "Transform HTML", menuItemControles: "opTransformHtmlPage" },
];

const vnpInnerOptions: Array<MenuItem> = [
  { title: "Get XML", menuItemControles: "opGetXmlPage" },
  { title: "Transform HTML", menuItemControles: "opTransformHtmlPage" },
];

const edmInnerOptions: Array<MenuItem> = vnpInnerOptions;

const fdoInnerOptions: Array<MenuItem> = vnpInnerOptions;

const qtInnerOptions: Array<MenuItem> = [
  { title: "Get XML", menuItemControles: "opGetXmlPage" },
];

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

export default function Sidebar({
  pageActiveState,
  setPageActiveState,
  toggleCollapsible,
}) {
  // console.log("From Sidebar pageActiveState", pageActiveState);
  // console.log("From Sidebar setPageActiveState", setPageActiveState);

  const [state, dispatch] = useReducer(reducer, initialState);

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

          <SidebarItem
            title="Order Paper"
            id="sb_op"
            isOpen={state.menuDropdownOP}
            Icon={DocumentIcon}
            onToggle={() => toggleDropdown("menuDropdownOP")}
            innerOptions={opInnerOptions}
          >
            <SidebarSubItem
              title="Get XML"
              id="opGetXmlPage"
              pageActiveState={pageActiveState}
              toggleCollapsible={toggleCollapsible}
              setPageActiveState={setPageActiveState}
            />
            <SidebarSubItem
              title="Transform HTML"
              id="opTransformHtmlPage"
              pageActiveState={pageActiveState}
              toggleCollapsible={toggleCollapsible}
              setPageActiveState={setPageActiveState}
            />
          </SidebarItem>

          {/* <SidebarItem
            title="Votes &amp; Proceedings"
            id="sb_vnp"
            isOpen={state.menuDropdownVnP}
            Icon={ConferenceIcon}
            onToggle={() => toggleDropdown("menuDropdownVnP")}
            innerOptions={vnpInnerOptions}
          /> */}

          {/* <SidebarItem
            title="Early Day Motions"
            id="sb_edm"
            isOpen={state.menuDropdownEDM}
            Icon={BriefcaseIcon}
            onToggle={() => toggleDropdown("menuDropdownEDM")}
            innerOptions={edmInnerOptions}
          />

          <SidebarItem
            title="Future Day Orals"
            id="sb_fdo"
            isOpen={state.menuDropdownFDO}
            Icon={CalenderIcon}
            onToggle={() => toggleDropdown("menuDropdownFDO")}
            innerOptions={fdoInnerOptions}
          />

          <SidebarItem
            title="Questions Tabled"
            id="sb_qt"
            isOpen={state.menuDropdownQT}
            Icon={SpeechBubbleIcon}
            onToggle={() => toggleDropdown("menuDropdownQT")}
            innerOptions={qtInnerOptions}
          /> */}
        </div>
      </div>

      <div className="version">
        <p>
          <small id="versionInfo">No version info</small>
        </p>
      </div>
    </div>
  );
}
