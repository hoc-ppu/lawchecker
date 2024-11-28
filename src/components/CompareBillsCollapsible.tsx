import Collapsible from "./Collapsible";
import Card from "./Card";
import Button from "./Button";
// import { PageActiveState } from "./App";
import { BodyProps } from "./Body";

// interface BodyProps {
//   pageActiveState: PageActiveState;
// }

const CompareBillsCollapsible: React.FC<BodyProps> = (props) => {
  return (
    <Collapsible
      isOpenState={props.pageActiveState}
      stateId="compareBillsCollapsible"
      title="Compare Bills"
    >
      <Card step="Introduction" info="">
        {/* You can put more than one button in here */}
        <p>
          You can create a report comparing two versions of a bill (e.g. as
          introduced and as amended in committee). You will need the XML files
          for each version to do this.
        </p>
        <p>
          Below, the rich comparison button will create a report with sections
          detailing the clauses that have been added and removed, changes to
          existing clauses, and changes to numbering of clauses. You can also
          compare the plain/unformatted text of the bills using a feature of{" "}
          <a href="https://code.visualstudio.com/">VS Code</a>. This includes
          changes to parts of the bill that are not within clauses or schedules.
          (e.g. titles.){" "}
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
            console.log("Select old file clicked");
            window.pywebview.api.open_file_dialog("com_bill_old_xml");
          }}
        />
        <small></small>
        <Button
          id="bill_newXMLfile"
          text="Select Newer XML File"
          handleClick={() => {
            console.log("Select folder clicked");
            window.pywebview.api.open_file_dialog("com_bill_new_xml");
          }}
        />
        <small></small>
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
          handleClick={() => {
            window.pywebview.api.bill_create_html_compare();
          }}
        />
        <Button
          id="bill_compareInVSCode"
          text="Open plain text comparison in VS Code"
          handleClick={() => {
            window.pywebview.api.bill_compare_in_vs_code();
          }}
        />
        <p className="mt-3">
          <small>
            <strong>Note:</strong> You must have VS code installed to open the
            plain text comparison.
          </small>
        </p>
      </Card>
    </Collapsible>
  );
};

export default CompareBillsCollapsible;