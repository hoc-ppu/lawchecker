/// <reference types="vite-plugin-svgr/client" />
import React, { useEffect, Dispatch, SetStateAction } from "react";
import UkParliamentSvg from "./../assets/ukParliament.svg?react";

import SidebarSubItem from "./SidebarSubItem";
import { PageActiveState } from "./App";
export interface MenuItem {
  title: string;
  menuItemControles: string;
}

async function getVersion(): Promise<string> {
  try {
    if (window.pywebview) {
      return await window.pywebview.api.get_version();
    } else {
      return "pywebview not available";
    }
  } catch (error) {
    console.error("Error getting version:", error);
    return "Error getting version";
  }
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

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const version = await getVersion();
        setVersionInfo(version);
      } catch (error) {
        console.error("Error fetching version:", error);
        setVersionInfo("Error loading version");
      }
    };

    fetchVersion();
  }, []);

  return (
    <div className="side-bar-top-level">
      {/* Begin Contents */}
      <div>
        <div className="figma-sidebar-navigation">
          <div className="logo-header mb-4">
            {/* TODO: I Don't think we want the <a/> here */}
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

          <SidebarSubItem
            title="Check Web Amendments"
            collapsibleId="checkAmendmentAPICollapsible"
            pageActiveState={pageActiveState}
            // toggleCollapsible={toggleCollapsible}
            setPageActiveState={setPageActiveState}
          />
        </div>
      </div>

      <div className="version">
        <small id="versionInfo">{versionInfo}</small>
      </div>
    </div>
  );
};

export default Sidebar;
