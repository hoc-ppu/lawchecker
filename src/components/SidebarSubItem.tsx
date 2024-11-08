import React, { SetStateAction, Dispatch } from "react";
import { PageActiveState } from "./App";

interface SidebarSubItemProps {
  title: string;
  collapsibleId: string;
  pageActiveState: PageActiveState;
  setPageActiveState: Dispatch<SetStateAction<PageActiveState>>;
}

const SidebarSubItem: React.FC<SidebarSubItemProps> = ({
  title,
  collapsibleId,
  pageActiveState,
  setPageActiveState,
}) => {
  function handleClick() {
    // reset all pageActiveState values to false

    const nextState: PageActiveState = { ...pageActiveState };
    for (const key in nextState) {
      nextState[key] = key === collapsibleId ? !nextState[key] : false;
    }

    setPageActiveState(nextState);
  }

  return (
    // Do we need the outer dive below?
    <div>
      <div
        key={`SubItem_${collapsibleId}`}
        className={`nav-collapsable-inner ${
          pageActiveState[collapsibleId] ? "active" : ""
        }`}
      >
        <div className="seleced-indicator"></div>
        <a
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
