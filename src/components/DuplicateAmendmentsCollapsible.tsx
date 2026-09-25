import React, { useState } from "react";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";
import addWordBreaksToPath from "./AddWordBreaksToPath";

const DuplicateAmendmentsCollapsible: React.FC<BodyProps> = (props) => {
  const [xml, setXml] = useState<string>("");

  const handleXml = async () => {
    let result = await window.pywebview.api.open_file_dialog("dup_amend_xml");
    result = addWordBreaksToPath(result);
    setXml(result);
  };

  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="duplicateAmendmentsCollapsible"
      title="Check Amendment Papers"
    >
      <Card step="Introduction" info="">
        {/* You can put more than one button in here */}
        <p>
          You can create a report showing any amendments with duplicate
          content.comparing consecutive versions of an amendment paper. You will
          need the LM XML file for an amendment paper.
        </p>
      </Card>
      <Card
        step="Step&nbsp;1"
        info="Select the amendment paper XML file to check for duplicates."
      >
        {/* You can put more than one button in here */}
        <Button
          id="dup_XMLfile"
          text="Select XML File"
          handleClick={handleXml}
        />

        {xml && (
          <small className="mt-3">
            <strong>XML File:</strong>{" "}
            <span dangerouslySetInnerHTML={{ __html: xml }} />
          </small>
        )}
        <p className="mt-3">
          <small>
            <strong>Note:</strong> The file must be a Lawmaker XML file.
          </small>
        </p>
      </Card>

      <Card step="Step&nbsp;2" info="Create the duplicate Amendments report">
        <Button
          id="bill_compareInBrowser"
          text="Create Report"
          handleClick={() => {
            console.log("Create report clicked");
            window.pywebview.api.dup_amend_html_report();
          }}
        />
      </Card>
    </Collapsible>
  );
};

export default DuplicateAmendmentsCollapsible;
