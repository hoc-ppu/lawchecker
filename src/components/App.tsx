import { useState, Dispatch, SetStateAction } from "react";
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
    checkAmendmentAPICollapsible: false,
  };

  const [pageActiveState, setPageActiveState]: [
    PageActiveState,
    Dispatch<SetStateAction<PageActiveState>>
  ] = useState(defaultPageOpenState);

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
