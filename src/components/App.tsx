import { useState, useEffect, Dispatch, SetStateAction } from "react";
import Sidebar from "./Sidebar";
import Body from "./Body";
// import { SectionOpenContext } from "./SectionOpenContext";

export interface PageActiveState {
  [key: string]: boolean;
}

const App: React.FC = () => {
  const defaultPageOpenState: PageActiveState = {
    compareBillsPage: false,
    compareAmendmentsPage: false,
    billNumberingPage: false,
    addedNamesPage: false,
  };

  const [pageActiveState, setPageActiveState]: [
    PageActiveState,
    Dispatch<SetStateAction<PageActiveState>>
  ] = useState(defaultPageOpenState);

  useEffect(() => {
    // Check if pywebview is available, then call the API
    if (window.pywebview) {
      window.pywebview.api.set_v_info();
      console.log("set_v_info called");
    }
  }, []);
  // function toggleCollapsible(key: string) {
  //   // reset all pageActiveState values to false

  //   const nextState = { ...pageOpenState };
  //   for (const k in nextState) {
  //     nextState[k] = k === key ? !nextState[k] : false;
  //   }

  //   setPageOpenState(nextState);
  // }
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
        pageActiveState={pageActiveState}
        setPageActiveState={setPageActiveState}
      />
      <Body pageActiveState={pageActiveState} />
    </div>
  );
};

export default App;
