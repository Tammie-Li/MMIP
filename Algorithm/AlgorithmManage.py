import numpy as np
import os
from Algorithm.EMGNet import EMGNet
from Algorithm.EEGNet import EEGNet
from Algorithm.CCA import SSVEP_CCA
from Algorithm.SimpleET import SimpleET


import torch
import os
import numpy as np
from sklearn import preprocessing
from scipy import signal
import numpy as np
from scipy.linalg import sqrtm, inv
import pickle
import copy


class DataProcess:
    def __init__(self):
        pass

    def scale_data(self, data):
        # 归一化数据 data = [N, C, T]
        scaler = preprocessing.StandardScaler()
        for i in range(data.shape[0]):
            data[i, :, :] = scaler.fit_transform(data[i, :, :])
        return data

    def band_pass_filter(self, data, freq_low, freq_high, fs):
        # 带通滤波
        f0 = 50.0
        Q = 5.0
        b1, a1 = signal.iirnotch(f0, Q, fs)
        wn = [freq_low * 2 / fs, freq_high * 2 / fs]
        b2, a2 = signal.butter(3, wn, "bandpass")
        for trial in range(data.shape[0]):
            data[trial, ...] = signal.filtfilt(b2, a2, data[trial, ...], axis=1)
            data[trial, ...] = signal.lfilter(b1, a1, data[trial, ...])
        return data

    def euclidean_space_alignment(self, data):
        """Transfer Learning for Brain–Computer Interfaces: A Euclidean Space Data Alignment Approach"""
        # data->(N, C, T), 需要先执行滤波操作
        # 公式10-计算协方差
        r = 0
        for trial in data:
            cov = np.cov(trial, rowvar=True)
            r += cov
        r = r / data.shape[0]
        # 公式11
        r_op = inv(sqrtm(r))

        results = np.matmul(r_op, data)
        return results

class AlgorithmManage(DataProcess):
    def __init__(self, algorithm_name, params):
        
        self.algorithm_name = algorithm_name
        num_classes = params["class"]
        drop_out = params["drop_out"]
        time_point = params["time_point"]
        channel = params["channel"]
        N_t = params["Nt"]
        N_s = params["Ns"]
        path = params["path"]
        if self.algorithm_name == "EMGNet":
            self.algorithm = EMGNet(num_classes, drop_out, time_point, channel, N_t, N_s)
            self.algorithm.load_state_dict(torch.load(path, map_location="cpu"))
        elif self.algorithm_name == "EEGNet":
            self.algorithm = EEGNet(num_classes)
        elif self.algorithm_name == "CCA":
            # 无训练SSVEP算法
            self.algorithm = SSVEP_CCA(samp_rate=250)
        elif self.algorithm_name == "SimpleET":
            # 眼动信号算法，根据绝对位置求解区域
            self.algorithm = SimpleET()


    def _pre_process_data(self, x):
        # 输入网络前，根据不同的要求，先完成预处理
        if self.algorithm_name == "EMGNet":
            x = self.band_pass_filter(data=x, freq_low=20, freq_high=150, fs=500)
        elif self.algorithm_name == "EEGNet":
            # 先降采样至256Hz
            # x = self.down_sample(x)
            x = self.band_pass_filter(data=x, freq_low=0.1, freq_high=48, fs=256)
        elif self.algorithm_name == "CCA":
            x = self.algorithm.pre_filter(x)
        return x


    def forward_inference(self, x):
        # 其中0是为了保持与深度学习方法一致的返回格式
        if self.algorithm_name == "SimpleET":
            res = self.algorithm.recognize(x)
            return 0, res
        if self.algorithm_name == "CCA":
            x = self._pre_process_data(x)
            res = self.algorithm.recognize(x)
            return 0, res

        self.algorithm.eval()
        x = self._pre_process_data(x)
        x = torch.tensor(x).float()
        y = self.algorithm(x)
        _, pred = torch.max(y, 1)
        return y, pred


