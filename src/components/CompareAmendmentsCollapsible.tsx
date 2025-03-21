import React, { useState } from "react";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";
import addWordBreaksToPath from "./AddWordBreaksToPath";

const CompareAmendmentsCollapsible: React.FC<BodyProps> = (props) => {
  const [isChecked, setIsChecked] = useState(false);
  const [oldXml, setOldXml] = useState<string>("");
  const [newXml, setNewXml] = useState<string>("");

  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setIsChecked(event.target.checked);
  };

  const handleOldXml = async () => {
    let result = await window.pywebview.api.open_file_dialog(
      "com_amend_old_xml"
    );
    result = addWordBreaksToPath(result);
    setOldXml(result);
  };

  const handleNewXml = async () => {
    let result = await window.pywebview.api.open_file_dialog(
      "com_amend_new_xml"
    );
    result = addWordBreaksToPath(result);
    setNewXml(result);
  };

  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="compareAmendmentsCollapsible"
      title="Check Amendment Papers"
    >
      <Card step="Introduction" info="">
        {/* You can put more than one button in here */}
        <p>
          You can create a report comparing consecutive versions of an amendment
          paper. This report will show you: Added and removed amendments, Added
          and removed names, Any stars that have not been changed correctly, and
          standing amendments with changes. You will need the LM XML files for
          both the older paper and the newer paper.
        </p>
        <p>
          If there are sitting days (or printing days) between the papers you
          are comparing, tick Days between papers . This is needed for the star
          check feature.{" "}
        </p>
      </Card>
      <Card
        step="Step&nbsp;1"
        info="Select the two amendment paper XML files that you would like to compare."
      >
        {/* You can put more than one button in here */}
        <Button
          id="bill_oldXMLfile"
          text="Select Older XML File"
          handleClick={handleOldXml}
        />
        <Button
          id="bill_newXMLfile"
          text="Select Newer XML File"
          handleClick={handleNewXml}
        />
        {oldXml && (
          <small className="mt-3">
            <strong>Older XML:</strong>{" "}
            <span dangerouslySetInnerHTML={{ __html: oldXml }} />
          </small>
        )}
        {newXml && (
          <small>
            <strong>Newer XML:</strong>{" "}
            <span dangerouslySetInnerHTML={{ __html: newXml }} />
          </small>
        )}
        <div className="form-check">
          <input
            className="form-check-input"
            type="checkbox"
            checked={isChecked}
            onChange={handleCheckboxChange}
            // value=""
            // id="flexCheckChecked"
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
        <Button
          id="bill_compareInBrowser"
          text="Create Report"
          handleClick={() => {
            console.log("Create report clicked");
            window.pywebview.api.amend_create_html_compare(isChecked);
          }}
        />
      </Card>
    </Collapsible>
  );
};

export default CompareAmendmentsCollapsible;
