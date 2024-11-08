/// <reference types="vite-plugin-svgr/client" />
import React, { useEffect, Dispatch, SetStateAction } from "react";
import UkParliamentSvg from "./../assets/ukParliament.svg?react";

import SidebarSubItem from "./SidebarSubItem";
import { PageActiveState } from "./App";
export interface MenuItem {
  title: string;
  menuItemControles: string;
}

interface SidebarProps {
  pageActiveState: PageActiveState;
  setPageActiveState: Dispatch<SetStateAction<PageActiveState>>;
}

const Sidebar: React.FC<SidebarProps> = ({
  pageActiveState,
  setPageActiveState,
}) => {
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
            collapsibleId="compareBillsCollapsible"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />
          <SidebarSubItem
            title="Bill Numbering"
            collapsibleId="billNumberingCollapsible"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />
          <SidebarSubItem
            title="Check Amendment Papers"
            collapsibleId="compareAmendmentsCollapsible"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />

          <SidebarSubItem
            title="Added Names Report"
            collapsibleId="addedNamesCollapsible"
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
