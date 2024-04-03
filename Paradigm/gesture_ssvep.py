import os, cv2
import warnings
import socket, threading
import numpy as np

from psychopy import visual, event, core
from loguru import logger
from Algorithm.AlgorithmManage import AlgorithmManage
from multiprocessing import Event, Queue
from Lib.Boruikang.neuracle import Neuracle
from Lib.Tang.emg import EMGRecoder
import copy
import time

from collections import Counter


warnings.filterwarnings("ignore")


# 类关系
# |---GestureSSVEPParadigm
# |---|---VideoStreamParadigm
# |---|---SSVEPParadigm
# |---|---EMGRecoder
# |---|---EEGRecoder
# |---|---EyeTrackingRecoder
# |---|---AlgorithmManage


class Status:
    def __init__(self):
        # 表示当前程序运行在何位置
        self.status = None
        # 表示系统目前接收到的最新命令
        self.command = None

class SSVEPParadigm:
    def __init__(self, win, refresh_rate = 30):

        self.window = win
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

        # 结束等待标志位
        self.stim_flag, self.show_flag = False, False

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

        # 红三角目标提示初始化
        self.triangle_tip_radius = 30
        self.triangle_tip = visual.Polygon(win=self.window, edges=3, units='pix', radius=self.triangle_tip_radius, fillColor='red',
                                      lineColor='red', pos=[0, 0])

        # 刺激文本初始化
        text_list = [str(i+1) for i in range(self.stim_num)]
        self.stim_text = []
        for i in range(self.stim_num):
            self.stim_text.append(visual.TextStim(self.window, text=text_list[i], pos=self.stim_pos[i], colorSpace="rgb255", color=self.stim_text_colors, height=70,
                                     autoLog=False))

    def show_init_ssvep_gui(self):
        # 显示系统初始化
        self.init_txt = visual.TextStim(win=self.window, text='已进入目标选择界面，请注视要选择的块，"开始"手势', pos=(-580, 440), height=60, color='red')
        self.init_txt.setPos([-580, 440])
        self.init_txt.draw()

        # 生成初始化帧
        globForm_init = visual.ElementArrayStim(self.window, nElements=self.stim_num, sfs=0, sizes=self.stim_size,
                                           xys=self.stim_pos, phases=0, colors=self.stim_colors, elementTex='sin',
                                           elementMask=None)
        self.stim_init = globForm_init

        self.stim_init.draw()
        for i in range(self.stim_num):
            self.stim_text[i].draw()
        self.window.flip()
        while self.stim_flag is not True:
            core.wait(0.1)

    def start_one_stim(self, time_length=2):
        start_stim_time = core.getTime()
        frame_num = 0
        while frame_num <= time_length * self.refresh_rate:
            self.stim.phases = self.stim_phase_0 + frame_num / self.refresh_rate * self.stim_frequency
            self.stim.draw()
            for i in range(self.stim_num):
                self.stim_text[i].draw()
            self.window.flip()
            frame_num = frame_num + 1
        end_stim_time = core.getTime()
        print(end_stim_time - start_stim_time)

    
    def show_result(self, res):
        # 根据用户的选择结果绘制结果提示
        res = 20
        x, y = self.stim_pos[res - 1]
        self.triangle_tip.fillColor = 'red'
        self.triangle_tip.lineColor = 'red'
        self.triangle_tip.setPos([x, y - self.stim_radius * 0.5 - self.triangle_tip_radius])

        self.init_txt.text = "眼动和脑电系统的综合判定为区域为---" + str(res) + ""
        self.init_txt.setPos([-345, 440])
        self.init_txt.draw()
        self.stim.phases = [0 for i in range(self.stim_num)]
        self.stim.draw()
        for i in range(self.stim_num):
            self.stim_text[i].draw()
        self.triangle_tip.draw()
        self.window.flip()
        while self.show_flag is not True:
            core.wait(0.1)
    
    def show_results_tips(self, message):
        self.init_txt.text = message
        self.init_txt.setPos([-700, 440])
        self.init_txt.draw()
        self.stim.phases = [0 for i in range(self.stim_num)]
        self.stim.draw()
        for i in range(self.stim_num):
            self.stim_text[i].draw()
        self.triangle_tip.draw()
        self.window.flip()
        while self.show_flag is not True:
            core.wait(0.1)

    def _calculate_pos(self):
        # 后续需要修改为根据刺激排列，计算刺激的位置
        self.stim_pos = []
        for idx in range(self.stim_num):
            # 屏幕最左端 + 左边留白 + 位置
            x_tmp = -960 + 105 + (self.stim_radius + 30) * (idx % 10)
            y_tmp = 540 - 280 - (self.stim_radius + 70) * (idx // 10)
            self.stim_pos.append([x_tmp, y_tmp])


class VideoStreamParadigm:
    def __init__(self, win):
        # 初始界面
        self.window = win
        self.init_txt = visual.TextStim(win=self.window, pos=(-100, 0), text='系统初始化完成，等待视频流', height=50, color='white')
        self.image = None
        self.close_flag = False

        self._init_receieve_image_server()


    def start(self):
        # 图片接收线程实时接收来自无人机的图像
        image_thread = threading.Thread(target=self.receive_video_stream)
        image_thread.start()

    def update(self):
        # psychopy实时显示视频流
        if self.image is not None:
            video_stream = visual.ImageStim(win=self.window, image=self.image)
        else:
            video_stream = self.init_txt
        video_stream.draw()
        self.window.flip()
    
    def close(self):
        self.close_flag = True


    def _init_receieve_image_server(self):
        # 初始化服务器
        # self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server.bind(("", 6666))
        # self.server.listen(1)
        # self.server.setblocking(False)
        # self.connect, addr = self.server.accept()

        # 设置相机捕获参数
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("Error: Could not open video stream.")
            core.quit()


    def receive_video_stream(self):
        # 通信部分，实时接受来自无人机的图像
        HOST = '127.0.0.1'
        PORT = 6666
        while not self.close_flag:
            # data, addr = self.server.recvfrom()
            # self.image = data

            # 暂时使用摄像头直接拍摄来模拟
            ret, frame = self.capture.read()
            if not ret:
                print("Error: Could not read frame from video stream.")
                break
            # 将 OpenCV 图像从 BGR 转换为 RGB 并归一化到 [-1, 1]
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 0)
            frame = frame / 255
            self.image = frame


class FixedSizeQueue:
    def __init__(self, size, init_val):
        self.queue = Queue(size)
        self.queue_list = []
        # 使用静息态满队
        for i in range(size):
            self.queue.put(init_val)
            self.queue_list.append(init_val)
    
    def update_fixed_size_queue(self, value):
        tmp = self.queue.get()
        self.queue.put(value)
        del(self.queue_list[0])
        self.queue_list.append(value)

    def get_the_smooth_command(self):
        # most_common(1) 返回一个列表，列表中的第一个元素是出现次数最多的元素及其次数
        counter = Counter(self.queue_list)
        most_common_element, most_common_count = counter.most_common(1)[0]  
        return most_common_element
    
class GestureSSVEPParadigm(Status):
    # 总范式，包括ssvep显示子范式和视频流实时显示子范式
    def __init__(self):
        self.window = visual.Window(size=(1920, 1080), units='pix', color=(-1, -1, -1),
                                    allowGUI=True, allowStencil=True, screen=-1)
        # SSVEP刺激系统时间长度
        self.t_len = 1

        # 记录当前系统处于哪个位置 0表示位于视频流系统，1表示处于SSVEP系统初始化界面，2表示处于SSVEP结果显示界面
        self.status = 0

        # 系统关闭标志，退出所有程序
        self.close_flag = False  

        # 系统接收到的最新指令，其中指令0表示静息态，保持不动，指令1表示由视频流系统切换至SSVEP初始化系统
        # 指令2表示开始SSVEP刺激，指令3表示由确认结果，发出指令，指令4表示由结果界面返回至视频流系统，
        # 指令5表示由结果界面返回至ssvep初始化界面，指令6表示结束所有程序。
        self.command = 0

        # 维护固定大小的队列用于记录最新的数据，标签平滑
        self.gesture_queue = FixedSizeQueue(100, 0)

        self.ssvep_mode = SSVEPParadigm(win=self.window, refresh_rate=30)
        self.video_mode = VideoStreamParadigm(win=self.window)

        # 初始化肌电手环参数
        emg_parm = {'port':'COM7', 'baudrate':460800}
        ctrparm = {}
        ctrparm['stopEv'] = Event()
        ctrparm['backQue'] = Queue()

        # pak_length, 需要维护缓冲区的长度，默认参数256表示实时更新0.5s的数据
        self.emg_recorder = EMGRecoder(emg_parm, ctrparm, pak_length=256)
        self.eeg_recorder = Neuracle(time_buffer=self.t_len)

        # 初始化肌电信号处理算法
        params_m = {"class": 5,
                  "drop_out": 0.4,
                  "time_point": 9,
                  "channel": 3,
                  "Nt": 8,
                  "Ns": 16,
                  "path": os.path.join(os.getcwd(), "Lib", "Checkpoint", "NUDTMEG_EMGNet_0119.pth")
        }

        # 初始化脑电信号处理算法
        params_e = {"class": 40,
                  "drop_out": 0.4,
                  "time_point": 32,
                  "channel": 64,
                  "Nt": 8,
                  "Ns": 16,
                  "path": os.path.join(os.getcwd(), "Lib", "Checkpoint", "NUDTMEG_EMGNet_0119.pth")
        }
        self.emg_algorithm = AlgorithmManage("EMGNet", params_m)
        self.eeg_algorithm = AlgorithmManage("EEGNet", params_e)

        # 定义向机器人系统发送的指令
        self.messsage = None

        # 初始化视频流系统
        self.video_mode.start()

    
    def status_monitor(self):
        # 实时监测肌电信号的指令，以便后续实现状态机的状态切换
        while not self.close_flag:
            logger.info('当前最新手势为:{}, 当前系统的状态为:{}'.format(self.command, self.status))
            # 获取最新的一组肌电信号，计算当前指令信息
            x = self.emg_recorder.get_data().reshape(1, 3, 256)
            time.sleep(0.005)
            gesture, pred = self.emg_algorithm.forward_inference(copy.deepcopy(x))
            # 通过指令平滑、更新指令
            self.gesture_queue.update_fixed_size_queue(pred.item())
            self.command = self.gesture_queue.get_the_smooth_command()

            if self.status == 1 and self.command == 2:
                self.ssvep_mode.stim_flag = True
            else:
                self.ssvep_mode.stim_flag = False
            if self.status == 2 and self.command != 2:
                self.ssvep_mode.show_flag = True
            else:
                self.ssvep_mode.show_flag = False

    def run(self):
        # 肌电信号处于长期运行状态，是整个系统运行的控制器和节拍器
        self.emg_recorder.start()
        # 等待2s, 确保获取足够长度的肌电信号
        core.wait(2)
        status_monitor_thread = threading.Thread(target=self.status_monitor)
        status_monitor_thread.start() 
        
        self.eeg_recorder.start()
        # 通过判断当前状态和当前指令实现状态机
        while not self.close_flag:
            if (self.status == 0 and self.command != 1) or (self.status == 2 and self.command == 0):
                self.video_mode.update()
                self.status = 0
            if (self.status == 0 and self.command == 1) or (self.status == 2 and self.command == 1):
                # self.video_mode.close()
                # 这里特别注意下面两行的顺序，不能替换
                self.status = 1
                self.ssvep_mode.show_init_ssvep_gui()
            if self.status == 1 and self.command == 2:
                # 这里特别注意下面两行的顺序，不能替换
                self.status = 2
                self.ssvep_mode.start_one_stim(self.t_len)
                x = self.eeg_recorder.get_data()
                logger.info('从设备中获取到一个脑电信号样本，数据形状为:{}'.format(x.shape))
                # res = self.eeg_algorithm.forward_inference(copy.deepcopy(x))
                res = 20
                self.ssvep_mode.show_result(res)
                # 指令预装载
                self.messsage = "区域--" + str(res) + "--消息已发送至机器人系统，指令0回到视频流观察 指令1重新选择，指令4结束"
            if self.status == 2 and self.command == 3:
                # 发送结果
                self.ssvep_mode.show_flag = True
                self.ssvep_mode.show_results_tips(self.messsage)
            if self.status == 2 and self.command == 4:
                # 退出所有程序
                self.video_mode.close()
                self.close_flag = True
                self.window.close()
                self.eeg_recorder.clear_buffer()
                self.eeg_recorder.stop()
                core.quit()
    
