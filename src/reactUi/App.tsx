import { useState, createContext } from "react";
import Formz from "./Formz";
import Sidebar from "./Sidebar";
import Body from "./Body";
import { SectionOpenContext } from "./SectionOpenContext";

function App() {
  const defaultPageOpenState = {
    opGetXmlPage: false,
    opTransformHtmlPage: false,
    edmGetXmlPage: false,
    edmTransformHtmlPage: false,
    vnpGetXmlPage: false,
    vnpTransformHtmlPage: false,
    fdoGetXmlPage: false,
    fdoTransformHtmlPage: false,
    qtGetXmlPage: false,
    qtTransformHtmlPage: false,
  };

  // const defaultIsAnimating = { ...defaultPageOpenState}
  // all is animating values are false
  // for (const key in defaultIsAnimating) {
  //   defaultIsAnimating[key] = false;
  // }

  const [pageOpenState, setPageOpenState] = useState(defaultPageOpenState);

  function toggleCollapsible(key: string) {
    // reset all pageActiveState values to false

    const nextState = { ...pageOpenState };
    for (const k in nextState) {
      nextState[k] = k === key ? !nextState[k] : false;
    }

    setPageOpenState(nextState);
  }
  // const toggleCollapsible = (key) => {
  //   if (!pageOpenState[key]) {
  //     setIsOpen(true); // Render the component
  //   } else {
  //     setIsAnimating(false); // Hide the component smoothly
  //     setTimeout(() => setIsOpen(false), 500); // Remove after animation
  //   }
  // };

  return (
    <div className="page">
      <Sidebar
        pageActiveState={pageOpenState}
        setPageActiveState={setPageOpenState}
        toggleCollapsible={toggleCollapsible}
      />
      <Body pageActiveState={pageOpenState} />
    </div>
  );
}

export default App;
