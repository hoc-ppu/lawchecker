import React from "react";
import Button from "./Button";

interface AccordionItemProps {
  title: string;
  children: React.ReactNode;
  isActive?: boolean;
  onToggle?: () => void;
}

const AccordionItem: React.FC<AccordionItemProps> = ({
  title,
  children,
  isActive,
  onToggle,
}) => {
  const cls = isActive ? "accordion-button" : "accordion-button collapsed";
  return (
    <div className={`accordion-item ${isActive ? "active" : ""}`}>
      <h2 className="accordion-header">
        <Button className={cls} text={title} handleClick={onToggle} />
      </h2>
      <div className={`accordion-collapse  ${isActive ? "show" : ""}`}>
        <div className="accordion-body">{children}</div>
      </div>
    </div>
  );
};

export default AccordionItem;
