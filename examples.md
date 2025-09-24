# Examples

Examples of using compare_report, compare_bills and an_report

## compare_report files

### Energy

```shell
compare_report example_files/amendments/energy_rm_rep_0904.xml example_files/amendments/energy_day_rep_0905.xml
```

### Data Protection and Digital Information (No. 2) Bill

```shell
compare_report example_files/amendments/datapro_rm_rep_0721.xml example_files/amendments/datapro_rm_rep_0825.xml
```
NC2 has incorrect star

### Economic Activity of Public Bodies (Overseas Matters) Bill

```shell
compare_report example_files/amendments/econactivity_rm_rep_0918.xml example_files/amendments/econactivity_rm_rep_0919.xml
```
Amendment 1 has changed content


### Victims and Prisoners Bill

```shell
compare_report -d example_files/amendments/victims_prisoners_rm_rep_0906.xml example_files/amendments/victims_prisoners_rm_rep_0908.xml
```
Note: -d as there is a sitting day between

## compare_bills files

### Data Protection and Digital Information Bill

```shell
compare_bills -c "example_files/bills/Data Protection and Digital Information Bill - commons introduced.xml" "example_files/bills/Data Protection and Digital Information Bill - commons committee.xml"
```
Note: -c will also do a compare in VS Code

### Social Housing (Regulation) Bill

```shell
compare_bills "example_files/bills/Social Housing (Regulation) Bill - lords committee.xml" "example_files/bills/Social Housing (Regulation) Bill - lords report.xml"
```

```shell
compare_bills -c "example_files/bills/Social Housing (Regulation) Bill - commons brl.xml" "example_files/bills/Social Housing (Regulation) Bill - commons committee.xml"
```


## Added Names Reprot


### Wednesday 28 June 2023

```shell
an_report example_files/addedNames/Dashboard_Data/2023-06-28__18-15_input_from_SP.xml --marshal='example_files/addedNames/Amendment_Paper_XML'
```


## Web amendments

```shell
web_amendments example_files/amendments/HL_Bill_134_Running_List_19_September.xml
```

Note: Once you have run this the first time, by default it will save a json file in the same folder and the xml file. On subsequent runs you can just run e.g.:

```shell
 web_amendments --json example_files/amendments/planning\ and\ infrastructure_report\ stage_amdts.json example_files/amendments/HL_Bill_134_Running_List_19_September.xml
 ```
