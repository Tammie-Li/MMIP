
"""描述：设备获取信号（包括脑电信号、表面肌肉电信号、以及眼动信号"""


import numpy as np
from Lib.Boruikang.readDataOnline import Neuracle


class sEMGDataReceive:
    def __init__(self):
        pass

class EyeTrackingDataReceive:
    def __init__(self):
        pass

class EEGDataRecPreProcess:
    """
    Description: 脑电信号获取、预处理
    Params: 
        device: 设备名称
        srate: 设备采样率
    """
    def __init__(self, device="boruikang", srate=1000):
        # 设备名称，主要面向boruikang，预留biosemi和neuroscan接口
        self.device = device
        self.srate = srate
        
    def _getData(self, timeLength):
        if self.device == "Boruikang":
            neuracle = Neuracle(time_buffer=timeLength, srate=self.srate)
            data = neuracle.get_data()
        elif self.device == "Biosemi":
            # biosemi = 
            pass
        return data

    def _preprocess(self, data):
        pass

    
    def forward(self, timeLength=1, sampleLength=1):
        """
        Input: 
            timeLength: 时间长度，从设备采集固定时间的脑电信号
            sampleLength: 用于样本划分，每一次推理过程使用的脑电时间长度
        Return: 
            data: 获取的脑电信号，已经做好分段处理(N x C x T)
        """
        if timeLength < sampleLength: assert("Error! timeLength should be set larger than sampleLength")

        orig_data = self._getData(timeLength)
        data = np.reshape(timeLength // sampleLength, orig_data.shape[0], sampleLength * self.srate)

        data = self._preprocess()

        return data

    def _clearBuf():
        pass