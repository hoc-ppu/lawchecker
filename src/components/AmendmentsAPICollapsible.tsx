import React, { useState } from "react";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";
import addWordBreaksToPath from "./AddWordBreaksToPath";

const CompareAmendmentsCollapsible: React.FC<BodyProps> = (props) => {
  const [lmXml, setLmXml] = useState<string>("");
  const [lmXmlFileSelected, setlmXmlFileSelected] = useState<boolean>(false);

  const handleLmXml = async () => {
    let result = await window.pywebview.api.open_file_dialog(
      "com_amend_api_xml"
    );
    result = addWordBreaksToPath(result);
    setLmXml(result);
  };
  const handleRefreshAPIamendments = async () => {};
  const handleCreateCSV = async () => {
    await window.pywebview.api.create_api_csv();
    console.log("create_api_csv called");
  };

  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="checkAmendmentAPICollapsible"
      title="Check Amendments API"
    >
      <Card step="Introduction" info="">
        {/* You can put more than one button in here */}
        <p>
          You can create a report summarising differences between amendments in
          the bills API and the in the LawMaker XML for a amendment paper or
          proceedings paper. This report will show you: Missing Amendments,
          Differences in names, and amendments that are not the same in both the
          paper and the API. You will need the LM XML file for the paper.
        </p>
      </Card>
      <Card
        step="Step&nbsp;1"
        info="Select an XML file for either amendment paper or proceedings paper ."
      >
        {/* You can put more than one button in here */}
        <Button
          id="api_billXMLfile"
          text="Select LM XML File"
          handleClick={handleLmXml}
        />
        {lmXml && (
          <small className="mt-3">
            <strong>LM XML:</strong>{" "}
            <span dangerouslySetInnerHTML={{ __html: lmXml }} />
          </small>
        )}
        <p className="mt-3">
          <small>
            <strong>Note:</strong> The file must be a Lawmaker XML file.
          </small>
        </p>
        {lmXml && (
          <Button
            id="refreshAPIamendments"
            text="Refresh API Amendments"
            handleClick={handleRefreshAPIamendments}
            className="btn btn-secondary"
          />
        )}
      </Card>

      <Card step="Step&nbsp;2" info="Create the Amendments API Check report">
        <Button
          id="api_report_in_browser"
          text="Create Report"
          handleClick={() => {
            console.log("Create report clicked");
            window.pywebview.api.create_api_report();
          }}
        />

        <Button
          id="api_report_CSV"
          text="Create CSV"
          handleClick={handleCreateCSV}
        />
      </Card>
    </Collapsible>
  );
};

export default CompareAmendmentsCollapsible;
