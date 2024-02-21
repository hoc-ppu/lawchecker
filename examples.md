# Examples

Sows how both compare_report and an_report

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



## Added Names Reprot


### Wednesday 28 June 2023

```shell
an_report _Reports/2023-06-28/Dashboard_Data/2023-06-28__18-15_input_from_SP.xml --marshal='_Reports/2023-06-28/Amendment_Paper_XML' -o=ANR2.html
```

