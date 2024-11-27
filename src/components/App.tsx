import { useState, useEffect, Dispatch, SetStateAction } from "react";
import Sidebar from "./Sidebar";
import Body from "./Body";
// import { SectionOpenContext } from "./SectionOpenContext";

export interface PageActiveState {
  [key: string]: boolean;
}

const App: React.FC = () => {
  const defaultPageOpenState: PageActiveState = {
    compareBillsCollapsible: false,
    compareAmendmentsCollapsible: false,
    billNumberingCollapsible: false,
    addedNamesCollapsible: false,
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
