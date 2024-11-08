import React, { useState, useEffect } from "react";
import { PageActiveState } from "./App";
// import "./SlidingComponent.css"; // Same CSS file

interface CollapsibleProps {
  isOpenState: PageActiveState;
  stateId: string;
  title: string;
  children: React.ReactNode;
}

const Collapsible: React.FC<CollapsibleProps> = ({
  isOpenState,
  stateId,
  title,
  children,
}) => {
  // const [isOpen, setIsOpen] = useState(false); // Controls visibility
  const [isAnimating, setIsAnimating] = useState(false); // Controls animation start

  useEffect(() => {
    if (isOpenState[stateId]) {
      // Trigger animation after the component is rendered
      // setTimeout(() => setIsAnimating(true), 500);
      setIsAnimating(true);
    } else {
      setTimeout(() => setIsAnimating(false), 500); // Stop animation when closing
    }
  }, [isOpenState, stateId]);

  return (
    // <div className="react-slider-container">
    //   <div className="react-slider-content">
    //     <h2>This is the underlying content.</h2>
    //   </div>

    /* Conditionally render the sliding component */
    (isOpenState[stateId] || isAnimating) && (
      <div
        className={`mb-5 react-slide-over ${
          isOpenState[stateId] && isAnimating ? "open" : "close"
        }`}
      >
        <h2 className="h4 mt-4 fw-normal">{title}</h2>
        {children}
      </div>
    )

    /* Trigger the slide behavior via parent-provided toggle */
    /* <button onClick={toggleCollapsible}>
        {isOpenState[key] ? "Close" : "Open"} Sliding Component
      </button>
    </div> */
  );
};

export default Collapsible;
