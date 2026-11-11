# Examples

Examples of using compare_report, compare_bills, an_report and web_amendments.

**Note:** These examples assume you installed LawChecker with uv. If you used pip, activate your virtual environment (if applicable) and leave `uv run ` off the start of each command.

## compare_report files

### Energy

```bash
uv run compare_report example_files/amendments/energy_rm_rep_0904.xml example_files/amendments/energy_day_rep_0905.xml
```
Nothing has moved.

### Data Protection and Digital Information (No. 2) Bill

```bash
uv run compare_report example_files/amendments/datapro_rm_rep_0721.xml example_files/amendments/datapro_rm_rep_0825.xml
```
NC2 has incorrect star

### Economic Activity of Public Bodies (Overseas Matters) Bill

```bash
uv run compare_report example_files/amendments/econactivity_rm_rep_0918.xml example_files/amendments/econactivity_rm_rep_0919.xml
```
Amendment 4 has changed content (line 5 became line 4).


### Victims and Prisoners Bill

```bash
uv run compare_report -d example_files/amendments/victims_prisoners_rm_rep_0906.xml example_files/amendments/victims_prisoners_rm_rep_0908.xml
```
Note: -d as there is a sitting day between

Amendment 1 has moved: it was after amendment 2, and is now before it.

### English Devolution and Community Empowerment Bill

```bash
uv run compare_report example_files/amendments/english_dev_rm_rep_1118.xml example_files/amendments/english_dev_rm_rep_1119.xml
```
44 amendments have moved, in 10 runs, all to Day Two. 38 amendments added and 3 removed (NC3, 67 and 68). The newer paper has headings (DAY ONE, DAY TWO); the older paper has none.

```bash
uv run compare_report example_files/amendments/english_dev_rm_pbc_1010.xml example_files/amendments/english_dev_rm_rep_1118.xml
```
These papers are from different stages (Committee and Report), so the report warns about it and leaves out the Amendment numbers and dnums, Moved amendments and Side-by-side order cards.

### Health Bill

```bash
uv run compare_report example_files/amendments/health_rm_rep_0901.xml example_files/amendments/health_rm_rep_0902.xml
```
52 amendments have moved, in 27 runs, all to the Second Day. The newer paper has headings (FIRST DAY, SECOND DAY); the older paper has none. The star check flags amendments 17 and 18, which are new but have no star.

```bash
uv run compare_report example_files/amendments/health_rm_rep_0902.xml example_files/amendments/health_rm_rep_0903.xml
```
7 amendments have moved, to 5 places, some from one day to the other (e.g. NC56 from the Second Day to the First Day). 52 amendments added.

```bash
uv run compare_report example_files/amendments/health_rm_rep_0903.xml example_files/amendments/health_rm_rep_0904.xml
```
NC63 has moved back to the Second Day, where it was in the 0902 paper. 1 amendment added.

```bash
uv run compare_report example_files/amendments/health_rm_rep_0904.xml example_files/amendments/health_day_rep_0907.xml
```
Nothing has moved, been added or been removed (checks for false alarms when the headings are in both papers).

```bash
uv run compare_report example_files/amendments/health_day_rep_0907.xml example_files/amendments/health_day_rep_0908.xml
```
The First Day's business has gone (166 amendments removed), and so have its headings.

## compare_bills files

### Data Protection and Digital Information Bill

```bash
uv run compare_bills -c "example_files/bills/Data Protection and Digital Information Bill - commons introduced.xml" "example_files/bills/Data Protection and Digital Information Bill - commons committee.xml"
```
Note: -c will also do a compare in VS Code

### Social Housing (Regulation) Bill

```bash
uv run compare_bills "example_files/bills/Social Housing (Regulation) Bill - lords committee.xml" "example_files/bills/Social Housing (Regulation) Bill - lords report.xml"
```

```bash
uv run compare_bills -c "example_files/bills/Social Housing (Regulation) Bill - commons brl.xml" "example_files/bills/Social Housing (Regulation) Bill - commons committee.xml"
```


## Added Names Report


### Wednesday 28 June 2023

```bash
uv run an_report example_files/addedNames/Dashboard_Data/2023-06-28__18-15_input_from_SP.xml --marshal='example_files/addedNames/Amendment_Paper_XML'
```


## Web amendments

`HL_Bill_134_Running_List_19_September.xml` is not in `example_files`, so use an amendment paper of your own. The first command needs internet access, because it gets the amendments from the Bills API.

```bash
uv run web_amendments example_files/amendments/HL_Bill_134_Running_List_19_September.xml
```

Note: Once you have run this the first time, by default it will save a json file in the same folder as the xml file. On subsequent runs you can just run e.g.:

```bash
uv run web_amendments --json "example_files/amendments/planning and infrastructure_report stage_amdts.json" example_files/amendments/HL_Bill_134_Running_List_19_September.xml
```
