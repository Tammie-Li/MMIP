import copy, time

from psychopy import visual, event, core
from Lib.Tang.emg import devicepro, EMGRecoder
import os, itertools
import numpy as np
import torch

from multiprocessing import Queue,Event
from Algorithm.AlgorithmManage import AlgorithmManage


class GestureEMGDataRecoder:
    """
    # 基于肌电信号的有动作手势识别数据采集类
    """
    def __init__(self, dev_para, exp_para, alg_para):
        """
        输入参数: 电腕带的设备参数(dict), 包括端口和波特率
                 实验范式的参数(dict), 包括trial的数量，block的数量，以及具体的实验名称
                 算法参数（dict）, 包括使用的算法名称，类别
        
        """
        self.finish_exp_flag = False
        self.last_label = -1
        self.block_cnt = 0
        self.trial_cnt = 0
        self.task_cnt = 0
        self.cur_step_func = self.__init_step_func

        self.__init_device_param(dev_para)
        self.__init_experiment_param(exp_para)
        self.__init_algorithm_param(alg_para)

        # 用于保存采集样本的数据 （N：samples x C: channels x T: timepoints）
        self.emgdata = []
        # 用于保存采集样本的标签 (N: samples)
        self.emglabel = []

    def __init_device_param(self, params):
        # 初始化设备参数
        self.ctrparm = {}
        self.ctrparm['stopEv'] = Event()
        self.ctrparm['backQue'] = Queue()

        self.emg_recoder = EMGRecoder(params, self.ctrparm)
        self.emg_recoder.start()
    
    def __init_experiment_param(self, params):
        # 初始化实验参数
        self.block_num = params['block_num']
        self.trial_num = params['trial_num']
        self.force_lib = params['force_array']
        # 总的手势识别训练任务数
        self.task_sum = params['trial_num'] * params['block_num'] * len(params['force_array'])
        self.frate = params['frate']
        self.fresh_cnt = params['trial_len'] * params['frate']
        self._image_path = os.path.join(os.getcwd(), "Lib", "Image", "finger.jpg")
        
    def __init_algorithm_param(self, params):
        # 初始化实验参数
        self.algorithm = AlgorithmManage("EMGNet", params)
        
    def run(self):
        while not self.finish_exp_flag:
            self.cur_step_func()
        self.close()

    def close(self):
        # 关闭psychopy窗口
        self.window.close()
        core.quit()

    def __init_step_func(self):
        """实验范式初始化"""
        self.alldata = []
        core.wait(4)
        # 定义psychopy窗口
        # 刺激和提示窗口
        self.window = visual.Window(size=(1000, 800), units='pix', color=(0.94, 0.94, 0.94),allowGUI=True, allowStencil=True, screen=-1)

        self.image = visual.ImageStim(win=self.window, pos=(0,-90), image=self._image_path)
        self.image.draw()

        self.res_img = []
        for i in range(5):
            path = os.path.join(os.getcwd(), 'Lib', 'Image', f'finger_{i+1:>02d}.jpg')
            img = visual.ImageStim(win=self.window, pos=(0, -90), image=path)
            self.res_img.append(img)

        # 显示消息文本
        self.info_text = visual.TextStim(win=self.window, anchorHoriz='center', anchorVert='center', text='准备，按[空格]开始',
                                         pos=(0,330), height=40, wrapWidth=1000, color='red')
        self.info_text.draw()

        self.ptexts = []
        self.atexts = []
        ppos = [(-240,-20),(-130,200),(20,240),(160,200),(260,100)]
        apos = [(-240, -60), (-130, 160), (20, 200), (160, 160), (260, 60)]
    
        for i in range(5):
            tm = visual.TextStim(win=self.window, anchorHoriz='center', anchorVert='center',
                                             text='',
                                             pos=ppos[i], height=30, wrapWidth=200, color='green')
            tm.draw()
            self.ptexts.append(tm)

        for i in range(5):
            tm = visual.TextStim(win=self.window, anchorHoriz='center', anchorVert='center',
                                             text='',
                                             pos=apos[i], height=30, wrapWidth=200, color='blue')
            tm.draw()
            self.atexts.append(tm)

        self.window.flip()

        self.cur_step_func = self.block_step_func

    def block_step_func(self):
        self.block_cnt += 1
        if self.block_cnt > self.block_num:
            self.cur_step_func = self.expend_step_fun
            return

        self.info_text = visual.TextStim(win=self.window, anchorHoriz='center',anchorVert='center',text='准备，按[空格]Block开始',
                                         pos=(0,330),height=40, wrapWidth=1000,color='red')
        self.info_text.draw()
        self.image.draw()
        self.window.flip()
        event.waitKeys(keyList=['space'])
        core.wait(1)

        self.cur_step_func = self.trial_step_func

    
    def trial_step_func(self):
        self.trial_cnt += 1
        if self.trial_cnt > self.trial_num:
            self.trial_cnt = 0
            self.cur_step_func = self.block_step_func
            return
        
        if self.trial_cnt > 1:
            self.info_text = visual.TextStim(win=self.window, anchorHoriz='center',anchorVert='center',text='休息一下，按[空格]继续',
                                            pos=(0,330),height=40, wrapWidth=1000,color='red')
            self.info_text.draw()
            self.image.draw()
            self.window.flip()
            event.waitKeys(keyList=['space'])
            core.wait(1)
        
        self.cur_step_func = self.task_step_func


    def task_step_func(self):
        task_list = self.force_lib

        for curtask in task_list:
            # 刷新所有需要刷新的对象
            self.task_cnt += 1
            self.info_text.setText(u'Block: %d, Trial: %d, 共计第%d/%d个任务'%(self.block_cnt, self.trial_cnt, self.task_cnt, self.task_sum))
            self.info_text.draw()
            self.image.draw()
            for i in range(5):
                self.ptexts[i].setText('')
                self.ptexts[i].draw()
            self.ptexts[curtask].setText('T: 手势' + str(curtask))
            self.ptexts[curtask].draw()
            self.window.flip()
            core.wait(0.5)
            # self.neuracle.clear_buffer()
            self.press_refresh_step_func(0.5, curtask)

            self.info_text.setText(u'Block: %d, Trial: %d, 共计第%d/%d个任务, 已完成'%(self.block_cnt, self.trial_cnt, self.task_cnt, self.task_sum))
            self.info_text.draw()
            self.image.draw()
            self.window.flip()
            core.wait(2)

        self.cur_step_func = self.trial_step_func

    def press_refresh_step_func(self, time_len, label):
        emg_res = 0
        # 刷新结果，经过计算，反馈速度为76Hz
        for i in range(self.fresh_cnt):

            # emg_res = label
            if i % (time_len * self.frate) == 0:
                emg_data = self.emg_recoder.get_data(0.5)
                # print(emg_data.T)
                emg_data = np.reshape(emg_data, (1,  emg_data.shape[0], emg_data.shape[1]))
                y, pred = self.algorithm.forward_inference(copy.deepcopy((emg_data)))
                pred = label
                print(pred)
                print(time.time())
                emg_res = pred
                self.emgdata.append(emg_data)
                self.emglabel.append(label)
            self.res_img[emg_res].draw()
            if self.last_label != label:
                self.window.flip()
            self.last_label = label
            # self.image.draw()

            self.info_text.setText(u'Block: %d, Trial: %d, 共计第%d/%d个任务'%(self.block_cnt, self.trial_cnt, self.task_cnt, self.task_sum))
            self.info_text.draw()
            for item in self.ptexts:
                item.draw()
            self.window.flip()
            core.wait(0.1)

    def expend_step_fun(self):
        self.info_text.setText(u'实验结束')
        self.info_text.draw()
        np.save(os.path.join(os.getcwd(), 'emgdata.npy'), np.array(self.emgdata))
        np.save(os.path.join(os.getcwd(), 'emglabel.npy'), np.array(self.emglabel))

        self.window.flip()
        core.wait(3)
        self.finish_experiment_flag = True

if __name__ == "__main__":

    dev_para = {'port':'COM3','baudrate':115200}
    exp_para = {'trial_num': 3,
                'trial_len': 400,
                'frate': 10,                          
                'screen_refresh_rate': 60,        
                'block_num': 2,
                'force_array': [0, 1, 2, 3, 4],  
                'press_level': [250]}
    a = GestureEMGDataRecoder(dev_para, exp_para)
    a.run()



    
    