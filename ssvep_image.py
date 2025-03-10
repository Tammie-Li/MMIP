from psychopy import visual, event, core
from Lib.Boruikang.neuracle import Neuracle
import numpy as np
import serial
import os
import numpy as np
from scipy import signal as scipysignal
from sklearn.cross_decomposition import CCA
import os


class Trigger:
    def __init__(self, com):
        self.ser = serial.Serial(com, 115200, timeout=0.5)
        if not self.ser.isOpen():
            self.ser.open()

    def send_trigger(self, num):
        trigger_list = [0x01, 0xe1, 0x01, 0x00, 0x01]
        trigger_list[-1] = num

        self.ser.write(trigger_list)

    def close_trigger(self):
        self.ser.close()


class SSVEPParadigm:
    def __init__(self, window):

        self.window = window

        # 全部按照75Hz的屏幕刷新率构建
        self.fresh_rate = 75

        # 刺激持续时间
        self.stim_time = 0.2

        # 刺激帧数
        self.stim_len = int(self.stim_time * self.fresh_rate)

        # 目标个数
        self.target_num = 40

        # 提示文字
        self.text = visual.TextStim(win=self.window, text="", pos=(0, 0), italic=False, color="white")
    
        # 加载ssvep帧
        stim_path = os.path.join(os.getcwd(), 'Lib', 'frame', 'stim')
        tips_path = os.path.join(os.getcwd(), 'Lib', 'frame', 'tips')
        result_path = os.path.join(os.getcwd(), 'Lib', 'frame', 'result')

        self.stim_list, self.tips_list, self.result_list = [], [], []

        for stim in range(self.stim_len):
            if stim % 10 == 0:
                self.text.text = f"实验范式准备中，刺激材料加载进度: {stim} / {self.stim_len}"
                self.text.draw()
                self.window.flip()
            path = os.path.join(stim_path, f"{stim:>02d}.png")
            self.stim_list.append(visual.ImageStim(win=self.window, image=path))
        
        for idx in range(self.target_num):
            if idx % 10 == 0:
                self.text.text = f"实验范式准备中，提示和结果范例加载进度: {stim} / {self.stim_len}"
                self.text.draw()
                self.window.flip()
            path = os.path.join(tips_path, f"{idx:>02d}.png")
            self.tips_list.append(visual.ImageStim(win=self.window, image=path))
            path = os.path.join(result_path, f"{idx:>02d}.png")
            self.result_list.append(visual.ImageStim(win=self.window, image=path))

        self.last_frame = visual.ImageStim(win=self.window, image=os.path.join(os.getcwd(), 'Lib', 'frame', 'last_frame.png'))

    def show_init_ssvep_gui(self, target_idx):
        # target_idx: 使用红三角提示被试注视的位置
        # 显示系统初始化
        self.tips_list[target_idx].draw()
        self.window.flip()
        event.waitKeys()


    def start_one_stim(self, time_length=2.2):
        start_stim_time = core.getTime()
        frame_num = 0
        while frame_num < self.stim_len:
            self.stim_list[frame_num].draw()
            self.window.flip()
            frame_num = frame_num + 1
        self.last_frame.draw()
        self.window.flip()
        end_stim_time = core.getTime()
        print(end_stim_time - start_stim_time)

    
    def show_result(self, res):
        # 根据用户的选择结果绘制结果提示
        res = res - 1 
        self.result_list[res].draw()
        self.window.flip()
        core.wait(1)


class SSVEPmethod:
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
        templ_time = 4
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


if __name__ == "__main__":
    isonline = True

    win = visual.Window(size=(1920, 1080), units='pix', color=(-1, -1, -1),
                        allowGUI=True, allowStencil=True, screen=-1)
    
    # 定义实验范式
    para = SSVEPParadigm(win)

    # 定义在线的脑电信号采集设备
    neuracle = Neuracle(time_buffer=0.2)

    # 定义SSVEP脑电信号处理算法
    algorithm = SSVEPmethod(samp_rate=250)

    # # 初始化
    # trigger_manage = Trigger(com="com6")

    BLOCK = 1
    TARGET = 40

    x, y = [], []
    neuracle.start()


    for block in range(BLOCK):
        print("Block: ", block+1)
        # trigger_manage.send_trigger(101)
        for target in range(TARGET):
            # 每显示10次，被试休息一次，防止疲劳

            para.show_init_ssvep_gui(target)

            # 前0.2s用于去基线，后4s用于训练样本
            # trigger_manage.send_trigger(120+target)
            para.start_one_stim(time_length=4.2)

            # 实时获取数据包
            data = neuracle.get_data()

            # 脑电信号处理，获取处理结果
            data = algorithm.pre_filter(data)
            result = algorithm.recognize(data)

            print(result)

            if isonline == False: result = target + 1

            # 实时反馈最终预测结果
            para.show_result(result+1)

            # 刺激程序端，在线数据收集
            x.append(data)
            y.append(target)

            neuracle.clear_buffer()
        # trigger_manage.send_trigger(102)
    
    # trigger_manage.close_trigger()
    neuracle.stop()
    
    print(np.array(x).shape, np.array(y).shape)
    np.save(os.path.join(os.getcwd(), "Dataset", "x.npy"), np.array(x))
    np.save(os.path.join(os.getcwd(), "Dataset", "y.npy"), np.array(y))

        