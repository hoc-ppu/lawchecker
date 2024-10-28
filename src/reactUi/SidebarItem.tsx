import React from "react";
import ExpandArrow from "./assets/ExpandArrow.svg?react";
import DocumentIcon from "./assets/documentIcon.svg?react";
import { MenuItem } from "./Sidebar";

interface SidebarItemProps {
  title: string;
  id: string;
  isOpen: boolean;
  Icon: React.ComponentType;
  onToggle: () => void;
  innerOptions: Array<MenuItem>;
  associatedPage: string | undefined;
  children?: React.ReactNode;
}

const getInnerOptionsObjects = (innerOptions: Array<MenuItem>, key: string) => {
  return innerOptions.map((option, i) => ({
    id: i,
    title: option.title,
    href: `#${key}_${option.title.replace(/\s/g, "_")}`,
    controles: option.menuItemControles,
  }));
};

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  id,
  isOpen,
  Icon,
  onToggle,
  innerOptions,
  children,
}) => {
  const innerOptionsObjects = getInnerOptionsObjects(innerOptions, id);

  const changeAssociatedPageState = (option) => {
    return function () {
      console.log(option.controles);
    };
  };

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

      {
        isOpen && children

        // <div>
        //   {innerOptionsObjects.map((option) => (
        //     <div key={option.id} className="nav-collapsable-inner">
        //       <div className="seleced-indicator"></div>
        //       <a
        //         href={option.href}
        //         // href="#get_XML_OP"
        //         // href="#transform_HTML_OP"
        //         // href="#EMs_For_Hansard_OP"
        //         role="button"
        //         className="concertina nav-item-text"
        //         onClick={changeAssociatedPageState(option)}
        //       >
        //         {option.title}
        //       </a>
        //     </div>
        //   ))}
        // </div>
      }
    </>
  );
};

export default SidebarItem;
