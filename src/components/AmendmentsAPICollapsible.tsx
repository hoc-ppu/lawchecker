import React, { useState } from "react";
import Accordion from "./Accordion";
import AccordionItem from "./AccordionItem";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";
import addWordBreaksToPath from "./AddWordBreaksToPath";

const CompareAmendmentsCollapsible: React.FC<BodyProps> = (props) => {
  const [lmXml, setLmXml] = useState<string>("");
  const [prettyLmXml, setPrettyLmXml] = useState<string>("");
  const [prettyApiAmdtsPath, setPrettyApiAmdtsPath] = useState<string>("");
  const [lmXmlFileSelected, setlmXmlFileSelected] = useState<boolean>(false);
  const [stageId, setStageId] = useState<string>("");
  const [billId, setBillId] = useState<string>("");
  const [saveJsonIsChecked, setSaveJsonIsChecked] = useState(true);

  const handleLmXml = async () => {
    const result = await window.pywebview.api.open_file_dialog(
      "com_amend_api_xml"
    );
    setLmXml(result);
    setPrettyLmXml(addWordBreaksToPath(result));
  };

  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSaveJsonIsChecked(event.target.checked);
  };

  const handleCreateCSV = () => {
    window.pywebview.api.create_api_csv();
    console.log("create_api_csv called");
  };

  const handleOpenApiAmdtsFile = async () => {
    console.log("Select JSON file clicked");
    const path = await window.pywebview.api.open_file_dialog(
      "existing_json_amdts"
    );
    setPrettyApiAmdtsPath(addWordBreaksToPath(path));
  };

  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="checkAmendmentAPICollapsible"
      title="Check Web Amendments"
    >
      <Card step="Introduction" info="">
        {/* You can put more than one button in here */}
        <p>
          You can create a report summarising differences between amendments on
          the parliament website and in the amendment paper or proceedings
          paper. This works by comparing LawMaker XML to JSON from the{" "}
          <a href="https://bills-api.parliament.uk/index.html" target="_blank">
            Bills API
          </a>{" "}
          (though you can also provide a previously downloaded JSON file). This
          report will show you: Missing Amendments, Differences in names, and
          amendments that are not the same in both the paper and the API. You
          will need the LM XML file for the paper.
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
        {prettyLmXml && (
          <small className="mt-3">
            <strong>LM XML:</strong>{" "}
            <span dangerouslySetInnerHTML={{ __html: prettyLmXml }} />
          </small>
        )}
        <p className="mt-3">
          <small>
            <strong>Note:</strong> The file must be a Lawmaker XML file.
          </small>
        </p>
      </Card>

      <Card step="Step&nbsp;2" info="Get or select the Amendments from the API">
        <Accordion>
          <AccordionItem title="Automatically get the Amendments from the API">
            <p>
              Use this option to Automatically query the bills API using
              information extracted from the XML file.
            </p>
            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                checked={saveJsonIsChecked}
                onChange={handleCheckboxChange}
                // value=""
                // id="flexCheckChecked"
              />
              <label className="form-check-label" htmlFor="flexCheckChecked">
                Save the JSON from the API
              </label>
            </div>
            <div className="d-grid gap-2 col-12 mx-auto my-3">
              <Button
                id="api_get_amendments_from_xml"
                text="Get Amendments"
                handleClick={() => {
                  console.log("Get Amendments clicked: ", lmXml);
                  window.pywebview.api.get_api_amendments_using_xml_for_params(
                    lmXml,
                    Boolean(saveJsonIsChecked)
                  );
                }}
              />
            </div>
          </AccordionItem>
          <AccordionItem title="Get the Amendments from the API using bill and stage IDs">
            <p>
              Use this option if you want to specify the precise bill ID and
              stage ID, or if the above option does not work. You can find the
              IDs by navigating to the relevant stage on the parliament website
              and coping the numbers from the url. E.g. in this URL{" "}
              <a
                target="blank"
                href="https://bills.parliament.uk/bills/3737/stages/19061"
              >
                https://bills.parliament.uk/bills/3737/stages/19061
              </a>{" "}
              the bill ID is 3737 and the stage ID is 19061
            </p>
            <div className="mb-3">
              <label htmlFor="billIdInput" className="form-label">
                Bill ID
              </label>
              <input
                type="number"
                className="form-control"
                id="billIdInput"
                placeholder="9999"
                onChange={(e) => setBillId(e.target.value)}
              />
            </div>
            <div className="mb-3">
              <label htmlFor="stageIdInput" className="form-label">
                Stage ID
              </label>
              <input
                type="number"
                className="form-control"
                id="stageIdInput"
                placeholder="9999"
                onChange={(e) => setStageId(e.target.value)}
              ></input>
            </div>
            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                checked={saveJsonIsChecked}
                onChange={handleCheckboxChange}
                // value=""
                // id="flexCheckChecked"
              />
              <label className="form-check-label" htmlFor="flexCheckChecked">
                Save the JSON from the API
              </label>
            </div>
            <div className="d-grid gap-2 col-12 mx-auto my-3">
              <Button
                id="api_get_amendments_from_ids"
                text="Get Amendments"
                handleClick={() => {
                  console.log("Get Amendments clicked");
                  console.log("billId", typeof billId);
                  window.pywebview.api.get_api_amendments_with_ids(
                    billId,
                    stageId
                  );
                }}
              />
            </div>
          </AccordionItem>
          <AccordionItem title="Select existing API Amendments JSON file">
            <p>Use this option to select a previously downloaded JSON file.</p>
            <div className="d-grid gap-2 col-12 mx-auto my-3">
              <Button
                id="api_get_amendments_from_file"
                text="Select JSON file"
                handleClick={handleOpenApiAmdtsFile}
              />
            </div>
            {prettyApiAmdtsPath && (
              <small className="mt-3">
                <strong>JSON file:</strong>{" "}
                <span
                  dangerouslySetInnerHTML={{ __html: prettyApiAmdtsPath }}
                />
              </small>
            )}
          </AccordionItem>
        </Accordion>
      </Card>

      <Card step="Step&nbsp;3" info="Check the amendments API">
        <p>
          Create a report dealing all the differences between amendments in the
          XML file and amendments on Bill.parliament.uk. Alternatively create a
          table with a row summarising the differences. This can be coppied to
          SharePoint.
        </p>
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
          text="Create data for SharePoint"
          handleClick={handleCreateCSV}
        />
      </Card>
    </Collapsible>
  );
};

export default CompareAmendmentsCollapsible;
