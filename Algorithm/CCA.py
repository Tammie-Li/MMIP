from psychopy import visual, event, core
from Lib.Boruikang.neuracle import Neuracle
import numpy as np
import serial
import os
import numpy as np
from scipy import signal as scipysignal
from sklearn.cross_decomposition import CCA
import os


class SSVEP_CCA:
    def __init__(self, samp_rate):
        self.cca = CCA(n_components=1)
        # 采样率
        self.samp_rate = samp_rate
        # 选择导联
        self.select_channel = range(50, 59)
        # 频率集合
        SSVEP_stim_freq = [8.0, 8.2, 8.4, 8.6, 8.8, 9.0, 9.2, 9.4, 9.6, 9.8,
                    10.0, 10.2, 10.4, 10.6, 10.8, 11.0, 11.2, 11.4, 11.6, 11.8,
                    12.0, 12.2, 12.4, 12.6, 12.8, 13.0, 13.2, 13.4, 13.6, 13.8,
                    14.0, 14.2, 14.4, 14.6, 14.8, 15.0, 15.2, 15.4, 15.6, 15.8]
        # 倍频数
        multiple_freq = 5

        # 偏移计算长度
        self.offset_len = int(0.2 * self.samp_rate)

        # 参考信号时间
        templ_time = 2
        # 参考信号长度
        self.templ_len = templ_time * self.samp_rate
        # 正余弦参考信号
        self.target_template_set = []
        # 采样点
        samp_point = np.linspace(0, (self.templ_len - 1) / self.samp_rate, int(self.templ_len), endpoint=True)
        # (1 * 计算长度)的二维矩阵
        samp_point = samp_point.reshape(1, len(samp_point))
        # 对于每个频率
        for freq in SSVEP_stim_freq:
            # 基频 + 倍频
            test_freq = np.linspace(freq, freq * multiple_freq, int(multiple_freq), endpoint=True)
            # (1 * 倍频数量)的二维矩阵
            test_freq = test_freq.reshape(1, len(test_freq))
            # (倍频数量 * 计算长度)的二维矩阵
            num_matrix = 2 * np.pi * np.dot(test_freq.T, samp_point)
            cos_set = np.cos(num_matrix)
            sin_set = np.sin(num_matrix)
            cs_set = np.append(cos_set, sin_set, axis=0)
            self.target_template_set.append(cs_set)

    # 识别算法
    def recognize(self, data):
        p = []
        data = data.T
        # 对每个频率
        for template in self.target_template_set:
            # 参考信号
            template = template[:, 0: data.shape[0]]
            template = template.T
            # 计算相关系数
            self.cca.fit(data, template)
            data_tran, template_tran = self.cca.transform(data, template)
            rho = np.corrcoef(data_tran[:,0],template_tran[:,0])[0, 1]
            p.append(rho)
        result = p.index(max(p))
        return result

    # 预处理
    def pre_filter(self, data):
        data = data[:, ::4]

        # 选择导联
        data = data[self.select_channel, :]

        # 去基线
        data = data[:, self.offset_len:] - np.tile(np.mean(data[:, :self.offset_len], -1).reshape(len(self.select_channel), 1), self.templ_len)

        # 滤波
        f0 = 50
        q = 35
        b, a = scipysignal.iircomb(f0, q, ftype='notch', fs=self.samp_rate)
        fs = self.samp_rate / 2
        N, Wn = scipysignal.ellipord([6 / fs, 90 / fs], [2 / fs, 100 / fs], 3, 40)
        b1, a1 = scipysignal.ellip(N, 1, 40, Wn, 'bandpass')
        filter_data = scipysignal.filtfilt(b1, a1, scipysignal.filtfilt(b, a, data))
        return filter_data
