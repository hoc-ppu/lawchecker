import React, { useState } from "react";
import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";

// interface BodyProps {
//   pageActiveState: PageActiveState;
// }

const AddedNamesCollapsible: React.FC<BodyProps> = (props) => {
  const [date, setDate] = useState<string>("");

  // Create working folder
  const handleCreateWorkingFolder = async () => {
    console.log("Creating working folder");
    const result = await window.pywebview.api.anr_create_working_folder(date);
    console.log("API call result:", result);
    alert(result); // Using a pop-up in lieu of modal for now
  };

  // Open dashboard data in browser
  const handleOpenDashboardData = async () => {
    console.log("Opening dashboard data in browser");
    const result = await window.pywebview.api.open_dash_xml_in_browser();
    console.log("API call result:", result);
    alert(result); // Show pop-up feedback
  };

   // Select dashboard XML file
  const handleSelectSPXML = async () => {
    console.log("Selecting dashboard XML file");
    const result = await window.pywebview.api.open_dash_xml_file();
    console.log("API call result:", result);
    alert(result); // Show pop-up feedback
  };
  
  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="addedNamesCollapsible"
      title="Added names report"
    >
      <Card step="Step&nbsp;1 Optional" info="Create working folders">
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
        />{" "}
        <span id="AN_DateSelected_1"></span>
        <Button
          id="AN_CreateWorkingFolder"
          text="Create working folder"
          handleClick={handleCreateWorkingFolder}
        />
        <p>
          Note: This button will also create subfolders, Dashboard_Data and
          Amendment_Paper_XML. Ideally save data from Sharepoint in
          Dashboard_Data and save Amendment XML in Amendment_Paper_XML (see
          below).
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
          computer (ideally within the folder created above). Then open that
          XML file using the button below.
        </p>
        <Button
          id="AN_Select_SP_XML"
          text="Select downloaded data"
          handleClick={handleSelectSPXML}
        />
      </Card>
      <Card step="Step&nbsp;3 (Optional)" info="Add marshalling info">
        <p>
          If you want the amendments in the report marshalling: save the XML
          file(s) for the paper(s) (downloaded LawMaker, or saved from
          FrameMaker) into a folder (ideally within the folder created above).
          Select that folder with the button below.
        </p>
        <Button id="AN_Select_Marshal_Dir" text="Select folder" />
        <p>
          Note: The marshalling feature works with one or several papers. In
          either case the XML file(s) need to be saved in a folder and you need
          to select that folder. Do not try to select a single XML file. Both LM
          and FM XML files can be used for marshalling.
        </p>
      </Card>

      <Card step="Step&nbsp;4" info="Open the added names report in a browser">
        <Button id="bill_compareInBrowser" text="Create Added Names Report" />
      </Card>
    </Collapsible>
  );
};

export default AddedNamesCollapsible;