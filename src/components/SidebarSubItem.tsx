import React, { SetStateAction, Dispatch } from "react";
import { PageActiveState } from "./App";

interface SidebarSubItemProps {
  title: string;
  id: string;
  pageActiveState: PageActiveState;
  setPageActiveState: Dispatch<SetStateAction<PageActiveState>>;
}

const SidebarSubItem: React.FC<SidebarSubItemProps> = ({
  title,
  id,
  pageActiveState,
  setPageActiveState,
}) => {
  function handleClick() {
    // reset all pageActiveState values to false

    const nextState: PageActiveState = { ...pageActiveState };
    for (const key in nextState) {
      nextState[key] = key === id ? !nextState[key] : false;
    }

    setPageActiveState(nextState);
  }

  return (
    // Do we need the outer dive below?
    <div>
      <div
        key={`SubItem_${id}`}
        className={`nav-collapsable-inner ${
          pageActiveState[id] ? "active" : ""
        }`}
      >
        <div className="seleced-indicator"></div>
        <a
          // href={href}
          // href="#get_XML_OP"
          // href="#transform_HTML_OP"
          // href="#EMs_For_Hansard_OP"
          role="button"
          className="concertina nav-item-text"
          onClick={handleClick}
        >
          {title}
        </a>
      </div>
    </div>
  );
};

export default SidebarSubItem;
