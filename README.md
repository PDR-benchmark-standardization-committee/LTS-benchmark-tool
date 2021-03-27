<div align="left">
<a href=https://www.facebook.com/pdr.bms/><img src="images/pdr_benchmark_logo.png" title="PDR Benchmark Commitee" width='300px'>
</div>

#  LTS-benchmark-tool
[日本語版(Japanese) README](README_JP.md)  
People who are involved in indoor positioning technology can calculate their estimation's indicator and requirement for xDR-based LTS (Localization and Tracking Systems).  
Indicator means evaluation value that is generally used for xDR-based LTS and requirement means validity that thajection is natural for real human behavior.  
You can calculate indicator and requiremet for demo estimation file and see how evaluation tool work.  
This evaluation tool has functions for saving indicator and requirement as csv and draw the histgrams and error deviation.  
This tool support following indicator and requirement.

| **Indcicator**           | **Description**    |
 ---                     |---                                       
| Circular Error (CE)                          | The distance between the ground-truth position and trajection position.|
| Circular Accuracy (CA)                       | The distance between the mode coordinates of the error XY distribution and origin (0, 0).| 
| Error Accumulation Gradient (EAG)            | The speed of error between trajection points and the correction points.|

| **Requirement**           | **Description**  |
 ---                     |---                    
| Requirement for Moving Velocity              | Check for trajection points velocity is within human walking speed (15 m/s) or not. The result in stdout is average velocity.|
| Requirement for Obstacle Avoidance           | Check for trajection points on map is the area that human cannot enter or not. The result in stdout is the ratio of coordinate where obstacle exists for total corrdinates. |

ALIP (Absolute Localization Inapplicable Period) : In ALIP, localization information such as BLE data cannot be used for estimation.

## Example of Evaluation Result 
<div align="cenetr">
<img src="images/result_graph.png" title="graph of indicator and requirements" width='700px'>
</div>

<img src="images/error_dist.png" title="error distribution" width='430px'><img src="images/CE_hist.png" title="CE histgram" width='400px'>
<img src="images/cumsum.png" title="cumulative sum" width='400px'>

## Requirement
```
python==3.6.10  
numpy==1.18.1  
pandas==1.0.1  
texttable==1.6.2  
tqdm==4.43.0  
opencv-python==4.2.0.34  
matplotlib==3.1.3 
scipy==1.4.1
seaborn==0.10.1  
```

## Description of Files

| **Filename**           | **Description**                                            |
 ---                     |---                                       
| main.py                | Execute evaluation script for indicator.                    | 
| indicator_evaluation.py| Module for calculating indicators.                          |
| dataloader.py          | Module for loading files.                                   |
| indicator_utils.py     | Specific functions to process indicators.                   |
| utils.py               | General functions to create result directory, stdout result.|
| demo_area_weights.ini  | Demo estimation's area weights.                             |
| requirements.txt       | Python library package version.                             |

## Usage
### Step.1 Install
```
git clone https://github.com/PDR-benchmark-standardization-committee/LTS-benchmark-tool
cd  LTS-benchmark-tool
pip install -r requirements.txt
```

### Step.2 Place estimation files
Place each track's estimation files at [estimatiion_folder]/PDR and [estimation_folder]/VDR respectively.  
If you want to evaluate demo estimation files, you don't need to prepare estimation files.
```
LTS-benchmark-tool/
    ├ estimation_folder/
    │       └ VDR/
    |         └ VDR_Traj_No*.txt [**VDR estimation files**]
    │       └ PDR/
    |         └ PDR_Traj_No*.txt [**PDR estimation files**]
    │
    ├ groud_truth_folder/
    |       ├ BLE_Beacon/
    |       |  └ BLE_info.csv
    |       |
    |       ├ VDR_ALIP/
    |       |  └ VDR_ALIP_info_No*.csv
    |       |
    |       ├ VDR_Ans/
    |       |  └ VDR_Ans_No*.csv
    |       |
    |       ├ VDR_Map/
    |       |  ├ Map_image.bmp
    |       |  ├ Map_size.csv
    |       |  └ VDR_Area.csv
    |       |
    |       ├ VDR_Module/
    |       |  └ VDR_Sens_No*.txt
    |       |
    |       ├ VDR_Ref/
    |       |  └ VDR_Ref_No*.csv
    |       |
    |       ├ PDR_ALIP/
    |       |  └ PDR_ALIP_info_No*.csv
    |       |
    |       ├ PDR_Ans/
    |       |  └ PDR_Ans_No*.csv
    |       |
    |       ├ PDR_Map/
    |       |  ├ Map_image.bmp
    |       |  ├ Map_size.csv
    |       |  └ PDR_Area.csv
    |       |
    |       ├ PDR_Module/
    |       |  └ PDR_Sens_No*.txt
    |       |
    |       ├ PDR_Ref/
    |       |  └ PDR_Ref_No*.csv
    |       |
    │       └ data_config.ini
    │
    ├ main.py
    ├ indicator_evaluation.py
    ├ indicator_utils.py
    ├ utils.py
    ├ dataloader.py
    ├ demo_area_weights.ini
    ├ requirements.txt
    └ README.md
```

The trajectry file contains positions of employees or folklifts at each time.

The data format is as follows:

0. Datetime (unixtime: second)
1. Position x (in meter)
2. Position y (in meter)

### Step.3 Place directory structure configuration 
You need to prepare configuration file that correspond to ground truth folder to evaluate.  
If you want to use your own groud truth file, please edit [ground_truth_folder/data_config.ini] and place at groud truth folder.  
```
; Folder name of answer data
[ANSWER]
ground_truth_dname = 'groud_truth_folder'

[PDR]
; Folder name of ground truth files for evaluation
map_dname = 'PDR_Map'
ans_dname = 'PDR_Ans'
ref_dname = 'PDR_Ref'
ALIP_dname = 'PDR_ALIP'
BLE_dname = 'BLE_Beacon'

; File name of ground truth files for evaluation
map_image_fname = 'Map_image.bmp'
map_size_fname = 'Map_size.csv'
area_fname = 'PDR_Area.csv'
ref_fname = 'PDR_Ref_No{}.csv'
ans_fname = 'PDR_Ans_No{}.csv'
ALIP_info_fname = 'PDR_ALIP_info_No{}.csv'
BLE_info_fname = 'BLE_info.csv'

; Color setting of drawing trajectory
map_obstacle_color = 'gray'
map_trajectory_color = 'green'
map_ref_color = 'orange'
map_ble_color = 'blue'

; Display size setting of drawing trajectory
map_trajectory_size = '0.2'
map_ref_size = '0.3'
map_ble_size = '2'
map_grid = 'False'

[VDR]
; Please write folder and file name for evaluation as [PDR]
```

#### About Map_size file
Size of target area in meter.  
X-length and Y-length are described in meter.  
Left bottom corner of the map is the origin of the map.

#### About Area file
If you want to evaluate the trajectory for each divided area, specify the area in this file.  
Enter the area number, the center coordinates of the area, 
and the vertical and horizontal lengths of the area on one line.

#### About Ref file
The file contains positions of employees or folklifts at each time.  
This data is used for trajectory estimation.  
The data format is the same as trajectory file

#### About Ans file
The file contains positions of employees or folklifts at each time.  
This data is not used for trajectory estimation.  
The data format is the same as trajectory file.

#### About ALIP_info file
ALIP stands for Absolute Localization Inapplicable Period. Previsouly we call this as BUP (BLE unreachable period).
In this period, BLE information is deleted from Sensor data.

The data format is as follows:

0. Start time of ALIP in Unixtime
1. End time of the ALIP in Unixtime

This is repeated for the number of ALIPs

### Step.4 Evaluation

Estimation and gorund truth folder path are required for command line argument.
```
python main.py [estimation_path] [ground_truth_path]
```
If you want evaluate demo estimation files, please execute following script.  
```
python main.py estimation_folder groud_truth_folder
```

Indicators results are saved at estimation files folder.  
See the resut in demo_estimation folder
```
estimation_folder/
  | VDR/
  | └ result/
  |    └ indicator
  |      ├ CA
  |      | ├ Traj_No*_area*_CA.png
  |      | └ Traj_No*_CA.csv
  |      |
  |      ├ CE
  |      | ├ CE_total_cumulative_sum.csv
  |      | ├ CE_total_cumulative_sum.png
  |      | ├ CE_total_histgram.png
  |      | ├ Traj_No*_CE.csv
  |      | ├ Traj_No*_CE_debug.csv
  |      | └ Traj_No*_CE_histgram.png
  |      |
  |      ├ EAG
  |      | ├ EAG_total_cumulative_sum.csv
  |      | ├ EAG_total_cumulative_sum.png
  |      | ├ EAG_total_histgram.png
  |      | ├ Traj_No*_EAG.csv
  |      | ├ Traj_No*_EAG_debug.csv
  |      | └ Traj_No*_EAG_histgram.png
  |      |
  |      ├ requirement_obstacle
  |      | └ Traj_No*_obstacle.csv
  |      |
  |      ├ requirement_velocity
  |      | └ Traj_No*_moving_velocity.csv
  |      |
  |      ├ Trajectory
  |      | └ Tra_No*.png
  |      |
  |      ├ file_indicator.csv
  |      └ total_indicator.csv
  | 
  └ PDR/
    └result/ [***Almost the same as VDR result folder***]
```

## Opptional Arguments
You can use opptional command line arguments below.  

### 1. Select track
You can select track to calculate indicator.   
In default, both VDR and PDR's indicator ande requirement are calculated.
```
python main.py estimation_folder groud_truth_folder --VDR --PDR
```

### 2. Select files
You can select specific estimatin file you want to evaluate.  
If you execute bellow script, [estimation_folder/VDR/VDR_Traj_No1.txt] indicator and requirement are evaluated.
```
python main.py estimation_folder groud_truth_folder --VDR --file VDR_Traj_No1.txt 
```

### 3. Select indicator
You can choose indicator and requirement to calculate.  
In default, all indicator and requirement are calculated.  

```
python main.py estimation_folder groud_truth_folder --CE --CA --EAG --requirement_velocity --requirement_obstacle  
```

### 4. Select parameters
You can select percentile to calculate for CE and EAG.  
In default, 50 percentile is calculated.  
```
python main.py estimation_folder groud_truth_folder --CE_percentile 30 --EAG_percentile 75
```

You can select velocity (default 1.5 m/s) for requirement fo moving velocity.  
```
python main.py estimation_folder groud_truth_folder --velocity 1.8
```

You can select band width to calculate CA by Kernel Density Estimation.  
If you do not select band_width, scipy default band width is used.  
```
python main.py estimation_folder groud_truth_folder --band_width 1.4
```

In default, CA is caluculated by Kernel Density Estimation, you can switch to use 2D histgram.    
```
python main.py estimation_folder groud_truth_folder --CA_hist
```

### 5. Use pre-defined area weights
You can use pre-defined area weights to calculate CA.  
You need to prepare area weights configuration ini file.  
Please see configuration format at [demo_area_weights.ini].  
If you do not select area weights configuration file path,  
area weights are set as the ratio of each area's answer points for total area answer points.  
```
; demo_area_weights.ini
[VDR]
area1 = 0.3
area2 = 0.3
area3 = 0.4

[PDR]
area1 = 0.4
area2 = 0.6
```
Please select area weigths configuration path
```
python main.py estimation_folder groud_truth_folder --area_weights demo_area_weights.ini
```

## Licence
Copyright (c) 2020 Satsuki Nagae and PDR benchmark standardization committee.  
LTS-benchmark-tool is open source software under the [MIT license](LICENSE).  

## Reference 
- [xDR Challenge in industrial Scenario in 2020](https://unit.aist.go.jp/harc/xDR-Challenge-2020/)  
- [Ryosuke Ichikari, Katsuhiko Kaji, Ryo Shimomura, Masakatsu Kourogi, Takashi Okuma, Takeshi Kurata: Off-Site Indoor Localization Competitions Based on Measured Data in a Warehouse, Sensors, vol. 19, issue 4, article 763, 2019.](https://www.mdpi.com/1424-8220/19/4/763/htm#)
