import copy
from psychopy import visual, event, core
from Lib.Tang.pressuredetector import Device
from Lib.Tang.emg import devicepro, Device2
from Lib.Boruikang.neuracle import Neuracle
import os, time, random, itertools, serial
import numpy as np
import torch

import multiprocessing
from multiprocessing import Queue,Event


class ActionGestureParadign:
    def __init__(self, exp_para): 
        self.finish_exp_flag = False
        self.last_label = -1
        self.block_cnt = 0
        self.trial_cnt = 0
        self.task_cnt = 0
        self.cur_step_func = self.__init_step_func
        # self.dev_para, dict{"port": , 'baudrate': , 'path': }
        # self.dev_para = dev_para
        # self.exp_para, dict{'trial_num': int->10,                  每个手指多少次 
        #                     'trial_len': int->10,                  每次按压持续的时间   
        #                     'frate': int,                          下位机参数
        #                     'screen_refresh_rate': int->60,        显示刷新的速率
        #                     'block_num': int->2,                   每个力度级别多少次
        #                     'force_array': array->[0, 1, 2, 3, 4],  定义有哪些手指按压任务
        #                     'press_level': array->[150, 400]}      定义有哪些力度级别
        self.exp_para = exp_para
        self.task_sum = self.exp_para['trial_num'] * self.exp_para['block_num'] * len(self.exp_para['force_array']) * len(self.exp_para['press_level'])
        self.fresh_cnt = self.exp_para['trial_len'] * self.exp_para['frate']
        self._image_path = os.path.join(os.getcwd(), "Lib", "Image", "finger.jpg")

        self.parm = {'port':'COM7','baudrate': 460800}
        self.ctrparm = {}
        self.ctrparm['stopEv'] = Event()
        self.ctrparm['backQue'] = Queue()

        self.emgdata = []
        self.emglabel = []

        alg_params = {"class": 5, "drop_out": 0.5, "time_point": 9, "channel": 3, "Nt": 8, "Ns": 16, "path": os.path.join(os.getcwd(), "Lib", "Checkpoint", "NUDTMEG_EMGNet_0119.pth")}
        self.algorithm = AlgorithmManage("EMGNet", alg_params)

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
        self.emg_device = Device2(self.parm, self.ctrparm)
        self.emg_device.start()

        # 定义psychopy窗口
        # 刺激和提示窗口
        self.window = visual.Window(size=(1000, 800), units='pix', color=(0.94, 0.94, 0.94),allowGUI=True, allowStencil=True, screen=-1)
        self.image = visual.ImageStim(win=self.window, pos=(0,-90), image=self._image_path)
        self.image.draw()

        self.res_img = []
        for i in range(5):
            path = os.path.join(os.getcwd(), 'Lib', 'Image', f'finger_{i+1:>02d}.jpg')
            img = visual.ImageStim(win=self.window, pos=(0,-90), image=path)
            self.res_img.append(img)

        # 显示消息文本
        self.info_text = visual.TextStim(win=self.window, anchorHoriz='center',anchorVert='center',text='准备，按[空格]开始',
                                         pos=(0,330),height=40, wrapWidth=1000,color='red')
        self.info_text.draw()


        self.window.flip()

        self.cur_step_func = self.block_step_func

    def block_step_func(self):
        self.block_cnt += 1
        if self.block_cnt > self.exp_para["block_num"]:
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
        if self.trial_cnt > self.exp_para["trial_num"]:
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
        press_array = self.exp_para['press_level'] 
        force_array = self.exp_para['force_array'] 
        task_list = itertools.product(force_array, press_array)

        for curtask in task_list:
            # 刷新所有需要刷新的对象
            self.task_cnt += 1
            self.info_text.setText(u'Block: %d, Trial: %d, 共计第%d/%d个任务'%(self.block_cnt, self.trial_cnt, self.task_cnt, self.task_sum))
            self.info_text.draw()
            self.image.draw()
            self.window.flip()
            core.wait(0.5)
            # self.neuracle.clear_buffer()
            self.press_refresh_step_func(0.5, curtask[0])
            # print(eeg_data)

            self.info_text.setText(u'Block: %d, Trial: %d, 共计第%d/%d个任务, 已完成'%(self.block_cnt, self.trial_cnt, self.task_cnt, self.task_sum))
            self.info_text.draw()
            self.image.draw()
            self.window.flip()
            core.wait(2)

        self.cur_step_func = self.trial_step_func

    def press_refresh_step_func(self, time, label):
        """刷新力的显示,预计力反馈为10Hz,进行10秒"""
        emg_res = 0
        # 这里要干的就是刷新力的显示,预计力反馈为10Hz,进行10秒
        for i in range(self.fresh_cnt):
            # emg_res = label
            if i % (time * self.exp_para['frate']) == 0:
                emg_data = self.emg_device.get_data(0.5)
                print(emg_data.T)
                emg_data = np.reshape(emg_data, (1,  emg_data.shape[0], emg_data.shape[1]))
                y, pred = self.algorithm.forward_inference(copy.deepcopy((emg_data)))
                # pred = label
                print(pred)
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
            # force = self.press_device.tweight
            # for j in range(5):
            #     self.atexts[j].setText('%.1fg'%(force[j]))
            #     self.atexts[j].draw()
            realtimeforce = []
            for text in self.atexts:
                realtimeforce.append(text.text)
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

    exp_para = {'trial_num': 3,
                'trial_len': 10,
                'frate': 10,                          
                'screen_refresh_rate': 60,        
                'block_num': 1,
                'force_array': [0, 1, 2, 3, 4],  
                'press_level': [250]}
    a = ActionGestureParadign(exp_para)
    a.run()



    
    