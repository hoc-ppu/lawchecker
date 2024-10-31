import clerk_logo from "./../assets/clerk_logo.svg";
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
              This includes changes to parts of the bill that are not within
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
                <a href="http://bills.parliament.uk/" target="_blank">
                  Parliament wedsite{" "}
                </a>
                should work{" "}
              </small>
            </p>
          </Card>

          <Card
            step="Step&nbsp;2"
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

        <Collapsible
          pageActiveState={pageActiveState}
          id="billNumberingPage"
          title="Bill Numbering"
        >
          <Card step="Introduction" info="">
            {/* You can put more than one button in here */}
            <p>
              Compare the numbering of sections (a.k.a. clauses) and schedule
              paragraphs in two or more versions of a UK parliament bill. The
              bills must be provided as LawMaker XML. The output is CSV file(s)
              which indicate when sections or schedule paragraphs are insearted
              or removed. You can also process several different bills at once,
              e.g. bill A (with 3 versions) and bill B (with 2 versions).{" "}
            </p>
          </Card>
          <Card
            step="Step&nbsp;1"
            info="Select a folder which contains Bill XML files."
          >
            {/* You can put more than one button in here */}
            <Button
              id="bill_oldXMLfile"
              text="Select Folder"
              handleClick={() => {
                console.log("Select folder clicked");
                // window.pywebview.api.op_working_dir.select_folder();
              }}
            />
            <p className="mt-3">
              <small>
                <strong>Note:</strong> Be sure to select a folder, not a file.
                The folder must contain at least two lawmaker XML files for the
                same bill (at different stages).
              </small>
            </p>
          </Card>

          <Card step="Step&nbsp;2" info="">
            <Button id="bill_compareInBrowser" text="Create CSV(s)" />
          </Card>
        </Collapsible>

        <Collapsible
          pageActiveState={pageActiveState}
          id="compareAmendmentsPage"
          title="Check Amendment Papers"
        >
          <Card step="Introduction" info="">
            {/* You can put more than one button in here */}
            <p>
              You can create a report comparing consecutive versions an
              amendment paper. This report will show you: Added and removed
              amendments, Added and removed names, Any stars that have not been
              changed correctly, and standing amendments with changes. You will
              need the XML files for each both the older paper and the newer
              paper.
            </p>
            <p>
              If there are sitting days (or printing days) between the papers
              you are comparing, tick Days between papers . This is needed for
              the star check feature.{" "}
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
            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                value=""
                id="flexCheckChecked"
              />
              <label className="form-check-label" htmlFor="flexCheckChecked">
                Days between papers
              </label>
            </div>
            <p className="mt-3">
              <small>
                <strong>Note:</strong> The files must be Lawmaker XML files.
              </small>
            </p>
          </Card>

          <Card step="Step&nbsp;2" info="Create the Amendments Check report">
            <Button id="bill_compareInBrowser" text="Create Report" />
          </Card>
        </Collapsible>

        <Collapsible
          pageActiveState={pageActiveState}
          id="billNumberingPage"
          title="Bill Numbering"
        >
          <Card step="Introduction" info="">
            {/* You can put more than one button in here */}
            <p>
              Compare the numbering of sections (a.k.a. clauses) and schedule
              paragraphs in two or more versions of a UK parliament bill. The
              bills must be provided as LawMaker XML. The output is CSV file(s)
              which indicate when sections or schedule paragraphs are insearted
              or removed. You can also process several different bills at once,
              e.g. bill A (with 3 versions) and bill B (with 2 versions).{" "}
            </p>
          </Card>
          <Card
            step="Step&nbsp;1"
            info="Select a folder which contains Bill XML files."
          >
            {/* You can put more than one button in here */}
            <Button
              id="bill_oldXMLfile"
              text="Select Folder"
              handleClick={() => {
                console.log("Select folder clicked");
                // window.pywebview.api.op_working_dir.select_folder();
              }}
            />
            <p className="mt-3">
              <small>
                <strong>Note:</strong> Be sure to select a folder, not a file.
                The folder must contain at least two lawmaker XML files for the
                same bill (at different stages).
              </small>
            </p>
          </Card>

          <Card step="Step&nbsp;2" info="">
            <Button id="bill_compareInBrowser" text="Create CSV(s)" />
          </Card>
        </Collapsible>

        <Collapsible
          pageActiveState={pageActiveState}
          id="compareAmendmentsPage"
          title="Check Amendment Papers"
        >
          <Card step="Introduction" info="">
            {/* You can put more than one button in here */}
            <p>
              You can create a report comparing consecutive versions an
              amendment paper. This report will show you: Added and removed
              amendments, Added and removed names, Any stars that have not been
              changed correctly, and standing amendments with changes. You will
              need the XML files for each both the older paper and the newer
              paper.
            </p>
            <p>
              If there are sitting days (or printing days) between the papers
              you are comparing, tick Days between papers . This is needed for
              the star check feature.{" "}
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
            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                value=""
                id="flexCheckChecked"
              />
              <label className="form-check-label" htmlFor="flexCheckChecked">
                Days between papers
              </label>
            </div>
            <p className="mt-3">
              <small>
                <strong>Note:</strong> The files must be Lawmaker XML files.
              </small>
            </p>
          </Card>

          <Card step="Step&nbsp;2" info="Create the Amendments Check report">
            <Button id="bill_compareInBrowser" text="Create Report" />
          </Card>
        </Collapsible>

        <Collapsible
          pageActiveState={pageActiveState}
          id="addedNamesPage"
          title="Added names report"
        >
          <Card step="Step&nbsp;1 Optional" info="Create working folders">
            {/* You can put more than one button in here */}
            <p>
              Ideally you should create a dated folder in{" "}
              <code>PPU - Scripts &gt; added_names_report &gt; _Reports </code>
              To do that click, 'Create Folder'.
            </p>
            <label htmlFor="opDate2" className="small">
              Select Date
            </label>
            <input id="opDate2" className="form-control" type="date" />{" "}
            <span id="opDateSelected_1"></span>
            <Button id="OP_selectHTMLfileBtn" text="Create working folder" />
            <p>
              Note: This button will also create subfolders, Dashboard_Data and
              Amendment_Paper_XML. Ideally save data form Shaprepoint in
              Dashboard_Data and save Amendment XML in Amendment_Paper_XML (see
              below).
            </p>
          </Card>
          <Card step="Step&nbsp;2" info="Download dashboard data">
            <Button
              id="OP_selectHTMLfileBtn"
              text="Open dashboard data in a Browser"
            />
            <p>
              The above button should open the added names dashboard data in a
              web browser. Once opened, you must download and save the XML to
              your computer (ideally within the folder created above). Then open
              that XML/text file using the button below.
            </p>
            <Button id="OP_selectHTMLfileBtn" text="Select downloaded data" />
          </Card>
          <Card step="Step&nbsp;3 (Optional)" info="Add marshalling info">
            <p>
              If you want the amendments in the report marshalling: save the XML
              file(s) for the paper(s) (downloaded LawMaker, or saved from
              FrameMaker) into a folder (ideally within the folder created
              above). Select that folder with the button below.
            </p>
            <Button id="OP_selectHTMLfileBtn" text="Select folder" />
            <p>
              Note: The marshalling feature works with one or several papers. In
              either case the XML file(s) need to be saved in a folder and you
              need to select that folder. Do not try to select a single XML
              file. Both LM and FM XML files can be used for marshalling.
            </p>
          </Card>

          <Card
            step="Step&nbsp;4"
            info="Open the added names report in a browser"
          >
            <Button
              id="bill_compareInBrowser"
              text="Create Added Names Report"
            />
          </Card>
        </Collapsible>
      </div>
    </div>
  );
};

export default Body;
