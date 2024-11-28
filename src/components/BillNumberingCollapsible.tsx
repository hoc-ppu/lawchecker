import React from "react";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";

const BillNumberingCollapsible: React.FC<BodyProps> = (props) => {
  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="billNumberingCollapsible"
      title="Bill Numbering"
    >
      <Card step="Introduction" info="">
        {/* You can put more than one button in here */}
        <p>
          Compare the numbering of sections (a.k.a. clauses) and schedule
          paragraphs in two or more versions of a UK parliament bill. The bills
          must be provided as LawMaker XML. The output is CSV file(s) which
          indicate when sections or schedule paragraphs are insearted or
          removed. You can also process several different bills at once, e.g.
          bill A (with 3 versions) and bill B (with 2 versions).{" "}
        </p>
      </Card>
      <Card
        step="Step&nbsp;1"
        info="Select a folder which contains Bill XML files."
      >
        {/* You can put more than one button in here */
        /* window.pywebview.api used to execute in main.py */}
        <Button
          id="bill_numberingSelectFolder"
          text="Select Folder"
          handleClick={() => {
            console.log("Select folder clicked");
            window.pywebview.api.select_folder("compare_number_dir");
          }}
        />
        <p className="mt-3">
          <small>
            <strong>Note:</strong> Be sure to select a folder, not a file. The
            folder must contain at least two lawmaker XML files for the same
            bill (at different stages).
          </small>
        </p>
      </Card>

      <Card step="Step&nbsp;2" info="">
        <Button id="bill_numberingCreateCSV" text="Create CSV(s)"
         handleClick={() => {
          console.log("Creating CSV");
          window.pywebview.api.compare_bill_numbering();
        }} />
      </Card>
    </Collapsible>
  );
};

export default BillNumberingCollapsible;
