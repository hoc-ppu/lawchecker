import React from "react";
import ExpandArrow from "./assets/ExpandArrow.svg?react";
import DocumentIcon from "./assets/documentIcon.svg?react";

interface SidebarItemProps {
  title: string;
  id: string;
  isOpen: boolean;
  Icon: React.ComponentType;
  onToggle: () => void;
  innerOptions: Array<string>;
}

const getInnerOptionsObjects = (innerOptions: Array<string>, key: string) => {
  return innerOptions.map((option, i) => ({
    id: i,
    title: option,
    href: `#${key}_${option.replace(/\s/g, "_")}`,
  }));
};

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  id,
  isOpen,
  Icon,
  onToggle,
  innerOptions,
}) => {
  const innerOptionsObjects = getInnerOptionsObjects(innerOptions, id);

  return (
    <>
      <div className="nav-item-outer-content" onClick={() => onToggle()}>
        <div className="op-nav">
          <Icon />
          <div>{title}</div>
        </div>
        <div className="sidebar-expand-arrow">
          <ExpandArrow />
        </div>
      </div>

      {isOpen && (
        <div>
          {innerOptionsObjects.map((option) => (
            <div key={option.id} className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href={option.href}
                // href="#get_XML_OP"
                // href="#transform_HTML_OP"
                // href="#EMs_For_Hansard_OP"
                role="button"
                className="concertina nav-item-text"
              >
                {option.title}
              </a>
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default SidebarItem;
