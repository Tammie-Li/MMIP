import os
from psychopy import visual, event, core
import numpy as np
from loguru import logger


class SSVEPParadigm:
    def __init__(self, refresh_rate = 30, ):

        self.window = visual.Window(size=(1920, 1080), units='pix', color=(-1, -1, -1),
                                    allowGUI=True, allowStencil=True, screen=-1)

        # 屏幕刷新率
        self.refresh_rate = refresh_rate
        
        # 40个刺激（可选择区域）4x10排列
        self.stim_c_num = 10
        self.stim_r_num = 4
        self.stim_num = self.stim_c_num * self.stim_r_num

        # 定义刺激频率
        # 频率为8，8.2，8.4，......, 15.8
        self.stim_frequency = np.arange(0, self.stim_num) * 0.2 + 8 
        
        logger.info('[paradigm] stimuli frequency: {}'.format(self.stim_frequency))

        # 刺激初始相位
        self.stim_phase_0 = 0   

        # 刺激尺寸
        self.stim_radius = 160

        # 刺激块背景颜色
        self.stim_colors = (1, 1, 1)

        # 刺激块文字颜色
        self.stim_text_colors = (0, 0, 0)

        x, y = np.meshgrid(np.arange(0, self.stim_c_num), np.arange(0, self.stim_r_num))
        
        # 留给文本显示的高度
        self.init_ver_hegith = 60

        # 计算刺激的位置
        self._calculate_pos()

        # 刺激初始化
        self.stim_size = [self.stim_radius, self.stim_radius]
        globForm = visual.ElementArrayStim(self.window, nElements=self.stim_num, sfs=0, sizes=self.stim_size,
                                           xys=self.stim_pos, phases=0, colors=self.stim_colors, elementTex='sin',
                                           elementMask=None)
        self.stim = globForm

        # 刺激文本初始化
        text_list = [str(i+1) for i in range(self.stim_num)]
        self.stim_text = []
        for i in range(self.stim_num):
            self.stim_text.append(visual.TextStim(self.window, text=text_list[i], pos=self.stim_pos[i], colorSpace="rgb255", color=self.stim_text_colors, height=70,
                                     autoLog=False))
            
        # 红三角目标提示初始化
        self.triangle_tip_radius = 30
        self.triangle_tip = visual.Polygon(win=self.window, edges=3, units='pix', radius=self.triangle_tip_radius, fillColor='red',
                                      lineColor='red', pos=[0, 0])

        # 显示系统初始化
        init_txt = visual.TextStim(win=self.window, text='已进入目标选择界面，请注视要选择的块，"开始"手势', pos=(-580, 440), height=60, color='red')
        # init_txt.setPos([-init_txt.width/4, init_txt.height*0.8])
        init_txt.draw()

        # 生成初始化帧
        globForm_init = visual.ElementArrayStim(self.window, nElements=self.stim_num, sfs=0, sizes=self.stim_size,
                                           xys=self.stim_pos, phases=0, colors=self.stim_colors, elementTex='sin',
                                           elementMask=None)
        self.stim_init = globForm_init

        self.stim_init.draw()
        for i in range(self.stim_num):
            self.stim_text[i].draw()
        self.window.flip()
        event.waitKeys()

    def start_one_stim(self, time_length):
        start_stim_time = core.getTime()
        frame_num = 0
        while frame_num <= time_length * self.refresh_rate:
            self.stim.phases = self.stim_phase_0 + frame_num / self.refresh_rate * self.stim_frequency
            self.stim.draw()
            for i in range(self.stim_num):
                self.stim_text[i].draw()
            # self.triangle_tip.draw()
            self.window.flip()
            frame_num = frame_num + 1
        end_stim_time = core.getTime()

        # 融合眼动和脑电算法获取结果
        res = 20

        x, y = self.stim_pos[res - 1]
        self.triangle_tip.fillColor = 'red'
        self.triangle_tip.lineColor = 'red'
        self.triangle_tip.setPos([x, y - self.stim_radius * 0.5 - self.triangle_tip_radius])
        self.triangle_tip.draw()
        print(end_stim_time - start_stim_time)
        self.window.flip()
        event.waitKeys()
        

    def _calculate_pos(self):
        # 后续需要修改为根据刺激排列，计算刺激的位置
        self.stim_pos = []
        for idx in range(self.stim_num):
            # 屏幕最左端 + 左边留白 + 位置
            x_tmp = -960 + 105 + (self.stim_radius + 30) * (idx % 10)
            y_tmp = 540 - 280 - (self.stim_radius + 70) * (idx // 10)
            self.stim_pos.append([x_tmp, y_tmp])


if __name__ == "__main__":
    para = SSVEPParadigm()


