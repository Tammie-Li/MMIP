import numpy as np
from numpy.core.shape_base import block
import warnings
import numpy as np
from psychopy import visual, event, core, parallel
from tqdm import tqdm, trange
import os
import time
import serial
from Algorithm.AlgorithmManage import AlgorithmManage
from Record.getData import EEGDataRecPreProcess, EyeTrackingDataReceive, sEMGDataReceive

warnings.filterwarnings("ignore")

class SSVEP_Paradigm:
    def __init__(self, stim_len, eeg=False, emg=False, eye=False):
        self.flag = False
        self.win = visual.Window(size=(1920, 1080), fullscr=False, colorSpace="rgb255", color=(0, 0, 0), screen=1)
        self.win.mouseVisible = False
        self.text = visual.TextStim(win=self.win, text="", height=0.1, pos=(0, 0), italic=False, color="white")

        self.frame_list = []
        self.frameRates = 60
        self.stim_num = stim_len * self.frameRates

        self.algorithm = AlgorithmManage("EEGNet", None)



    def __read_img(self):
        print("载入图片")
        for i in range(self.stim_num):
            if i % 10 == 0:
                self.text.text = f"范式准备进度: {i} / {self.stim_num}"
                self.text.draw()
                self.win.flip()
            frame_path = os.path.join("Lib/frame/stim", f"0_{i}.png")
            self.frame_list.append(visual.ImageStim(win=self.win, image=frame_path))

    def run(self):
        while(self.flag):
            # 实验准备范式
            visual.ImageStim(win=self.win, image=f"Lib/frame/000.jpg").draw()
            self.text.text = f"请做好准备，准备完成后按空格开始！"
            self.text.draw()
            self.win.flip()
            event.waitKeys()

            # SSVEP刺激过程
            startTime = time.time()
            for frame in self.frame_list:
                frame.draw()
                self.win.flip()
            print(f"耗时: {time.time() - startTime}")

            # 从穿戴式设备中获取数据
            if self.eeg:
                eeg_data = EEGDataRecPreProcess



