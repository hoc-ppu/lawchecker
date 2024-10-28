import pup_logo from "./../assets/pup_logo.svg";
import Card from "./Card";
import Button from "./Button";
import Collapsible from "./Collapsible";
import { PageActiveState } from "./App";

interface BodyProps {
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
        <div id="app-home react-slider-content">
          {/* previously the above had className="collapse show" */}
          <img
            className={`pup-logo py-3 ${
              noActivePage ? "unblurred" : "blurred"
            }`}
            style={{ width: "50%" }}
            src={pup_logo}
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
        <Collapsible
          pageActiveState={pageActiveState}
          id="compareBillsPage"
          title="Compare Bills"
        >
          <Card step="Introduction" info="">
            {/* You can put more than one button in here */}
            <p>
              You can create a report comparing two versions of a bill (e.g. as
              introduced and as amended in committee). You will need the XML
              files for each version to do this.
            </p>
            <p>
              Below, the rich comparison button will create a report with
              sections detailing the clauses that have been added and removed,
              changes to existing clauses, and changes to numbering of clauses.
              You can also compare the plain/unformatted text of the bills using
              a feature of <a href="https://code.visualstudio.com/">VS Code</a>.
              This includes changes to parts of the bill which are not within
              clauses or schedules. (e.g. titles.){" "}
            </p>
          </Card>
          <Card
            step="Step&nbsp;1"
            info="Select the two bill XML files that you would like to compare."
          >
            {/* You can put more than one button in here */}
            <Button
              id="bill_oldXMLfile"
              text="Select Older XML File"
              handleClick={() => {
                console.log("Select folder clicked");
                // window.pywebview.api.op_working_dir.select_folder();
              }}
            />
            <Button
              id="bill_newXMLfile"
              text="Select Newer XML File"
              handleClick={() => {
                console.log("Select folder clicked");
                // window.pywebview.api.op_working_dir.select_folder();
              }}
            />
            <p className="mt-3">
              <small>
                <strong>Note:</strong> The files must be Lawmaker XML files. XML
                files on the{" "}
                <a
                  href="http://services.orderpaper.parliament.uk/"
                  target="_blank"
                >
                  Parliament wedsite
                </a>
                should work{" "}
              </small>
            </p>
          </Card>

          <Card
            step="Step&nbsp;3"
            info="Select how you would like to see a compare."
          >
            <Button
              id="bill_compareInBrowser"
              text="Open rich comparison in Browser"
            />
            <Button
              id="bill_compareInVSCode"
              text="Open plain text comparison in VS Code"
            />
            <p className="mt-3">
              <small>
                <strong>Note:</strong> You must have VS code installed to open
                the plain text comparison.
              </small>
            </p>
          </Card>
        </Collapsible>
      </div>
    </div>
  );
};

export default Body;
