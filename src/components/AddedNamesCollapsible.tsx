import React, { useState } from "react";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
import addWordBreaksToPath from "./AddWordBreaksToPath";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";

// interface BodyProps {
//   pageActiveState: PageActiveState;
// }

const AddedNamesCollapsible: React.FC<BodyProps> = (props) => {
  const [date, setDate] = useState<string>("");
  const [workingFolderPath, setWorkingFolderPath] = useState<string>("");
  const [selectedSPXML, setSelectedSPXML] = useState<string>("");
  const [marshalDir, setMarshalDir] = useState<string>("");

  // Create working folder
  const handleCreateWorkingFolder = async () => {
    // console.log("Creating working folder");
    const result = await window.pywebview.api.anr_create_working_folder(date);
    // console.log("API call result:", result);

    if (result.startsWith("Working folder created: ")) {
      setWorkingFolderPath(result.replace("Working folder created: ", ""));
    }
  };

  // Open folder in file explorer
  const handleOpenFolder = async (folderPath: string) => {
    // console.log("Opening folder in file explorer");
    const result = await window.pywebview.api.open_folder(folderPath);
    // console.log("API call result:", result);
  };

  // Open dashboard data in browser
  const handleOpenDashboardData = async () => {
    // console.log("Opening dashboard data in browser");
    const result = await window.pywebview.api.open_dash_xml_in_browser();
    // console.log("API call result:", result);
  };

  // Select dashboard XML file
  const handleSelectSPXML = async () => {
    console.log("Selecting dashboard XML file");
    try {
      let fileResult: string = await window.pywebview.api.open_dash_xml_file();
      // console.log("API call result:", fileResult);

      if (fileResult.startsWith("Selected file: ")) {
        fileResult = fileResult.replace("Selected file: ", "");
        fileResult = addWordBreaksToPath(fileResult);
        setSelectedSPXML(fileResult); // Update state with file path
        // console.log("File path set successfully:", fileResult);
      } else {
        console.error("Unexpected fileResult format:", fileResult);
      }
    } catch (error) {
      console.error("Error selecting file:", error);
    }
  };

  // Select marshalling XML directory
  const handleSelectMarshalDir = async () => {
    console.log("Selecting amendment XML directory");
    let result: string = await window.pywebview.api.anr_open_amd_xml_dir();
    // console.log("API call result:", result);
    if (result.startsWith("Selected directory: ")) {
      result = result.replace("Selected directory: ", "");

      // Replace both backslashes and forward slashes with
      // `Word Break Opportunity` tag followed by the slash
      result = addWordBreaksToPath(result);

      setMarshalDir(result);
    }
  };

  // Clear selected directory
  const handleClearSelectedDir = () => {
    console.log("Clearing selected directory");
    setMarshalDir("");
  };

  // Execute the report generation and clear marshalling directory
  const handleCreateReport = async () => {
    console.log("Creating report");
    const result = await window.pywebview.api.anr_run_xslts();
    // console.log("API call result:", result);
    clearMarshalDirAfterReport();
  };

  // Clear marshalling directory path after report generation
  const clearMarshalDirAfterReport = () => {
    setMarshalDir("");
  };

  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="addedNamesCollapsible"
      title="Added names report"
    >
      <Card step="Step&nbsp;1 (Optional)" info="Create working folders">
        {/* You can put more than one button in here */}
        <p>
          Ideally you should create a dated folder in{" "}
          <code>PPU - Scripts &gt; added_names_report &gt; _Reports </code>
          To do that click, 'Create Folder'.
        </p>
        <label htmlFor="AN_Date" className="small">
          Select Date
        </label>
        <input
          id="AN_Date"
          className="form-control"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <span id="AN_DateSelected_1"></span>
        <Button
          id="AN_CreateWorkingFolder"
          text="Create working folder"
          handleClick={handleCreateWorkingFolder}
        />
        {workingFolderPath && (
          <p className="mt-3">
            <strong>Working folder:</strong>{" "}
            <a href="#" onClick={() => handleOpenFolder(workingFolderPath)}>
              {workingFolderPath}
            </a>
          </p>
        )}
        <p>
          <small>
            <strong>Note:</strong> This button will also create subfolders,
            Dashboard_Data and Amendment_Paper_XML. Ideally save data from
            Sharepoint in Dashboard_Data and save Amendment XML in
            Amendment_Paper_XML (see below).
          </small>
        </p>
      </Card>
      <Card step="Step&nbsp;2" info="Download dashboard data">
        <Button
          id="AN_OpenDashboardData"
          text="Open dashboard data in a Browser"
          handleClick={handleOpenDashboardData}
        />
        <p>
          The above button should open the added names dashboard data in a web
          browser. Once opened, you must download and save the XML to your
          computer (ideally within the folder created above). Then open that XML
          file using the button below.
        </p>
        <Button
          id="AN_Select_SP_XML"
          text="Select downloaded data"
          handleClick={handleSelectSPXML}
        />
        {selectedSPXML && (
          <p className="mt-3">
            <strong>Selected file:</strong>{" "}
            <span dangerouslySetInnerHTML={{ __html: selectedSPXML }} />
          </p>
        )}
      </Card>
      <Card step="Step&nbsp;3 (Recommended)" info="Add marshalling info">
        <p>
          If you want the amendments in the report marshalling: save the
          Lawmaker XML file(s) for the paper(s) into a folder (ideally within
          the folder created above). Select that folder with the button below.
        </p>
        <Button
          id="AN_Select_Marshal_Dir"
          text="Select folder"
          handleClick={handleSelectMarshalDir}
        />
        {marshalDir && (
          <>
            <p className="mt-3">
              <strong>Marshalling data:</strong>{" "}
              <span dangerouslySetInnerHTML={{ __html: marshalDir }} />
            </p>
            <Button
              id="AN_ClearSelectedDir"
              text="Cancel use of marshalling data"
              handleClick={handleClearSelectedDir}
            />
          </>
        )}
        <p>
          <small>
            <strong>Note:</strong> The marshalling feature works with one or
            several papers. In either case the{" "}
            <strong>
              XML file(s) must be saved in a folder and you need to select that
              folder.
            </strong>{" "}
            Do not try to select a single XML file.
          </small>
        </p>
      </Card>

      <Card step="Step&nbsp;4" info="Open the added names report in a browser">
        <Button
          id="AN_CreateReport"
          text="Create Added Names Report"
          handleClick={handleCreateReport}
        />
      </Card>
    </Collapsible>
  );
};

export default AddedNamesCollapsible;
