# Examples

Sows how both compare and an_report

## Compare files

### Energy
```shell
compare LM_XML/energy_rm_rep_0901.xml LM_XML/energy_rm_rep_0904.xml
```

```shell
compare LM_XML/energy_rm_rep_0904.xml LM_XML/energy_day_rep_0905.xml
```

### Data Protection and Digital Information (No. 2) Bill
```shell
compare LM_XML/datapro_rm_rep_0720.xml LM_XML/datapro_rm_rep_0721.xml
```

```shell
compare LM_XML/datapro_rm_rep_0721.xml LM_XML/datapro_rm_rep_0825.xml
```
NC2 has incorrect star

### Digital Markets, Competition and Consumers Bill
```shell
compare LM_XML/digital_rm_rep_0721.xml LM_XML/digital_rm_rep_0825.xml
```

```shell
compare LM_XML/digital_rm_rep_0825.xml LM_XML/digital_rm_rep_0906.xml
```

### Economic Activity of Public Bodies (Overseas Matters) Bill
```shell
compare LM_XML/econactivity_day_pbc_0914.xml LM_XML/econactivity_rm_rep_0915.xml
```

```shell
compare LM_XML/econactivity_rm_rep_0915.xml LM_XML/econactivity_rm_rep_0918.xml
```

```shell
compare LM_XML/econactivity_rm_rep_0918.xml LM_XML/econactivity_rm_rep_0919.xml
```
Amendment 1 has changed content

```shell
compare LM_XML/econactivity_rm_rep_0919.xml LM_XML/econactivity_rm_rep_0920.xml
```

### Victims and Prisoners Bill

```shell
compare -d LM_XML/victims_prisoners_rm_rep_0906.xml LM_XML/victims_prisoners_rm_rep_0908.xml
```
Note: -d as there is a sitting day between

```shell
compare LM_XML/victims_prisoners_rm_rep_0908.xml LM_XML/victims_prisoners_rm_rep_0912.xml
```

## Added Names Reprot


### Wednesday 28 June 2023

```shell
an_report _Reports/2023-06-28/Dashboard_Data/2023-06-28__18-15_input_from_SP.xml --marshal='_Reports/2023-06-28/Amendment_Paper_XML' -o=ANR2.html
```

### Wednesday 30 August 2023
```shell
an_report _Reports/2023-08-30/Dashboard_Data/2023-08-30__16-11_input_from_SP.xml --marshal=_Reports/2023-08-30/Amendment_Paper_XML/ -o=ANR.html
```

### Thursday 24 August 2023
```shell
an_report _Reports/2023-08-24/Dashboard_Data/2023-08-24__15-36_input_from_SP.xml --marshal='_Reports/2023-08-24/Amendment_Paper_XML' -o=ANR.html
```
