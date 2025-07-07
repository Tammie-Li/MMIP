## A Unified Brain-Eye-Hand Multi-Modal Interface for Human-Robot Interaction: Design and Validation
**Author**: Hongxin Li, Zongtan Zhou, Yaru Liu*, Pengmin Zhu, Yimin Hu, Jingsheng Tang, Junhao Xiao, and Huimin Lu 

**Institution**: The College of Intelligence Science and Technology, National University of Defense Technology

## Abstract
Advanced human-computer interface (HCI) based on multimodal physiological signals, such as Electroencephalogram (EEG), Electromyogram (EMG), and eye tracking, holds transformative potential for human-robot interaction (HRI). However, their adoption in real-world robotic applications has been limited due to the lack of systematic validation. To bridge the gap between HCI and robotics, a unified Brain-Eye-Hand Multi-Modal Interface (BEH-MMI) was designed that supports multi-modal HCI inputs and real-time dynamic visualization of mobile robots. The BEH-MMI consists of three components: a multi-modal human-computer interface (MHCI), a multi-robot semi-physical experimental platform (MSEP), and an intermediate software framework for system integration. The MHCI seamlessly integrates three physiological signal inputs (EEG, EMG, and eye tracking) and supports multiple experimental paradigms, such as steady-state visual evoked potentials and gesture recognition. The MSEP features multiple cost-effective omnidirectional wheeled mobile robots and multi-touch screens, enabling dynamic scene rendering and robot movement according to programmed instructions. The BEH-MMI liberates researchers from hardware and software implementation details, allowing them to concentrate on developing HCI methods without constraints imposed by fixed scenarios, tasks, or interfaces. To validate the functionality and performance, we conducted a three-phase experimental protocol: single-modal interaction testing, multimodal integration task evaluation, and practical robot application expansion. 

## Overview
![overview](/Lib/overview.png "The overall architecture of the MMIP")
consists of the human-robot interaction system and the multi-robot semi-physical experimental system. It supports interaction interfaces for three modalities, e.g. EEG, EMG, and eye-tracking, thereby providing support for human-robot simulation experiments.

## Environmental requirements
```txt
python >= 3.6
torch >= 1.7.0
numpy >= 1.20
psychopy >= 2023.1.3
scipy >= 1.6.2
```

## Usage
### 1. Single-modal Interaction Test 
```python ssvep_image.py``` or ```python ssvep_stimulate.py```
 
### 2. Quantitative Analysis
Please refer to the program in the following link[https://github.com/Tammie-Li/sEMG-GF], whose data processing method is consistent with it

### 3. Multi-modal Semi-Physics Comprehensive Experiment 
```python main.py``` 

modified the value **paradigm_name = "semi-physics"**


### 4. Multi-modal Physics Comprehensive Validation
```python main.py```

modified the value **paradigm_name = "physics"**

## Disclaimer 
This project is released under the GNU General Public License (GPL). By using, modifying, or distributing this software, you agree to comply with the terms of the GPL. The authors and contributors of this project are not liable for any damages or issues arising from the use of this software. Use at your own risk. For more details, refer to the GPL license.
