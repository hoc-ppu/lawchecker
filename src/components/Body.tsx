import clerk_logo from "./../assets/clerk_logo.svg";
import CompareBillsCollapsible from "./CompareBillsCollapsible";
import BillNumberingCollapsible from "./BillNumberingCollapsible";
import CompareAmendmentsCollapsible from "./CompareAmendmentsCollapsible";
import AmendmentsAPICollapsible from "./AmendmentsAPICollapsible";
import AddedNamesCollapsible from "./AddedNamesCollapsible";
import { PageActiveState } from "./App";

export interface BodyProps {
  pageActiveState: PageActiveState;
}

const Body: React.FC<BodyProps> = ({ pageActiveState }) => {
  const noActivePage = Object.values(pageActiveState).every(
    (value) => value === false
  ); /* Adjust the duration and easing as needed */

  return (
    <div className="main-content-top-level">
      <div className="top-title-container">
        <h1>Law Checker</h1>
      </div>

      <div className="main-content-inner react-slider-container">
        <div className="mt-4"> {/* Intentionally left empty*/} </div>
        <div id="app-home react-slider-content" className="mt-5">
          {/* previously the above had className="collapse show" */}
          <img
            className={`pup-logo py-3 ${
              noActivePage ? "unblurred" : "blurred"
            }`}
            style={{ width: "25%" }}
            src={clerk_logo}
            alt="LawChecker logo"
          />
          <h2
            className={`h3 py-5 text-center ${
              noActivePage ? "unblurred" : "blurred"
            }`}
          >
            Please select from the&#8201;&nbsp;
            <strong>options on the left</strong>
          </h2>
        </div>
        <div className="">
          <div className="text-center small">
            Please report bugs or improvement ideas to Mark Fawcett or Richard
            Martin.
            <br />
            Code avaliable on{" "}
            <a href="https://github.com/hoc-ppu/lawchecker" target="_blank">
              Github
            </a>
            .
          </div>
        </div>

        <CompareBillsCollapsible pageActiveState={pageActiveState} />
        <BillNumberingCollapsible pageActiveState={pageActiveState} />
        <CompareAmendmentsCollapsible pageActiveState={pageActiveState} />
        <AddedNamesCollapsible pageActiveState={pageActiveState} />
        <AmendmentsAPICollapsible pageActiveState={pageActiveState} />
      </div>
    </div>
  );
};

export default Body;
