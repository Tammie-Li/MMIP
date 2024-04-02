
"""描述：设备获取信号（包括脑电信号、表面肌肉电信号、以及眼动信号"""


import numpy as np
from Lib.Boruikang.readDataOnline import Neuracle
from Lib.Tang.emg import EMGRecoder
from multiprocessing import Event, Queue


class sEMGDataReceive:
    def __init__(self, parm):
        # parm = {'port':'COM8', 'baudrate':460800}
        ctrparm = {}
        ctrparm['stopEv'] = Event()
        ctrparm['backQue'] = Queue()

        # pak_length, 需要维护缓冲区的长度，默认参数256表示实时更新0.5s的数据
        self.emg_recorder = EMGRecoder(parm, ctrparm, pak_length=256)
    
    def start_record_data(self):
        self.emg_recorder.start()
    
    def get_fix_time_length_data(self):
        # 取出缓冲区内的数据
        emg_data = self.emg_recorder.get_data()
        return emg_data

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