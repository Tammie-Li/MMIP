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
from Lib.EyeTrack.client import EyeTrackerClient
import copy
import time
import struct

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

class PhysicsParadigm:
    def __init__(self, window):
        self.window = window
        # 屏幕刷新率
        self.refresh_rate = 75
        
        # 刺激持续时间
        self.stim_time = 2.2

        # 刺激帧数
        self.stim_len = int(self.stim_time * self.refresh_rate)

        # 目标个数
        self.target_num = 40

        # 提示文字
        self.text = visual.TextStim(win=self.window, text="", height=50, color="white", pos=(-400, 0))
    
        # 加载ssvep帧
        stim_path = os.path.join(os.getcwd(), 'Lib', 'frame', 'stim')
        tips_path = os.path.join(os.getcwd(), 'Lib', 'frame', 'tips')
        result_path = os.path.join(os.getcwd(), 'Lib', 'frame', 'result')

        self.stim_list, self.tips_list, self.result_list = [], [], []

        self.stim_flag, self.show_flag = False, False

        for stim in range(self.stim_len):
            if stim % 10 == 0:
                self.text.text = f"实验范式准备中，刺激材料加载进度: {stim} / {self.stim_len}"
                self.text.draw()
                self.window.flip()
            path = os.path.join(stim_path, f"{stim:>02d}.png")
            self.stim_list.append(visual.ImageStim(win=self.window, image=path))
        
        for idx in range(self.target_num):
            if idx % 10 == 0:
                self.text.text = f"实验范式准备中，提示和结果范例加载进度: {idx} / {self.target_num}"
                self.text.draw()
                self.window.flip()
            path = os.path.join(tips_path, f"{idx:>02d}.png")
            self.tips_list.append(visual.ImageStim(win=self.window, image=path))
            path = os.path.join(result_path, f"{idx:>02d}.png")
            self.result_list.append(visual.ImageStim(win=self.window, image=path))
    
        self.last_frame = visual.ImageStim(win=self.window, image=os.path.join(os.getcwd(), 'Lib', 'frame', 'last_frame.png'))
        self.init_frame = visual.ImageStim(win=self.window, image=os.path.join(os.getcwd(), 'Lib', 'frame', 'init_frame.png'))

    def show_init_ssvep_gui(self):
        # 显示系统初始化
        # 简单说明被试需要做的事情
        self.init_frame.draw()
        self.window.flip()
        while self.stim_flag is not True:
            core.wait(0.1)

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
        while self.show_flag is not True:
            core.wait(0.1)
    
    def show_results_tips(self, message):
        self.text.text = message
        self.text.draw()
        self.window.flip()
        core.wait(1)
        while self.show_flag is not True:
            core.wait(0.1)


class VideoStreamParadigm:
    def __init__(self, win):
        # 初始界面
        self.window = win
        self.init_txt = visual.TextStim(win=self.window, pos=(-100, 0), text='系统初始化完成，等待视频流', height=50, color='white')
        self.image = None
        self.close_flag = False

        self._init_receieve_image_server()


    def start(self):
        image_thread = threading.Thread(target=self.receive_video_stream)
        image_thread.start()

    def update(self):
        # psychopy实时显示视频流
        # 暂时使用摄像头直接拍摄来模拟

        if self.image is not None:
            video_stream = visual.ImageStim(win=self.window, image=self.image, size=(1920, 1080))
            video_stream.draw()
        self.window.flip()
    
    def close(self):
        self.close_flag = True


    def _init_receieve_image_server(self):
        # 初始化服务器
        # 设置TCP通信相关参数
        server_ip = '192.168.1.101'          # 服务器IP地址
        server_port = 12345              # 服务器端口号
        self.buffer_size = 1024        # 接收缓冲区大小

        # 创建TCP套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 连接到服务器
        self.sock.connect((server_ip, server_port))
        logger.info('已与机器人终端建立通信连接，准备图像传输')

    def receive_video_stream(self):
        # 通信部分，实时接受来自无人机的图像
        while not self.close_flag:
            # 接收图像大小数据
            img_size_data = self.sock.recv(4)

            # 解析图像大小数据
            img_size = struct.unpack('I', img_size_data)[0]

            # 接收图像数据
            img_data = b''
            while len(img_data) < img_size:
                data = self.sock.recv(min(self.buffer_size, img_size - len(img_data)))
                if not data:
                    break
                img_data += data

            # 将图像数据解码成图像
            frame = cv2.imdecode(np.frombuffer(img_data, dtype=np.uint8), 1)

            frame = cv2.resize(frame, (1920, 1080))

            grid_spacing = 192
            # 在图像上绘制网格线
            for i in range(0, frame.shape[1], grid_spacing):
                cv2.line(frame, (i, 312), (i, frame.shape[0]), (0, 255, 0), 1)

            for j in range(312, frame.shape[0], grid_spacing):
                cv2.line(frame, (0, j), (frame.shape[1], j), (0, 255, 0), 1)

            for label in range(40):
                pos_h, pos_w = (label%10)*192, 312+label//10*192
                if label >=10: pos_h = pos_h - 8
                cv2.putText(img=frame, text=str(label+1), org=(pos_h+96-2, pos_w+96+10), fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, color=(0, 0, 255), thickness=2, lineType=4)

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
        self.t_len = 2.2

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

        # 控制端接口，用于控制机器人前往区域，以及对单个机器人实现精确控制
        self.control_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.ssvep_mode = SSVEPParadigm(window=self.window)
        self.video_mode = VideoStreamParadigm(win=self.window)


        # 初始化肌电手环参数
        emg_parm = {'port':'COM3', 'baudrate':460800}
        ctrparm = {}
        ctrparm['stopEv'] = Event()
        ctrparm['backQue'] = Queue()

        # pak_length, 需要维护缓冲区的长度，默认参数256表示实时更新0.5s的数据
        # 测试通信时，可以注释以下代码，摆脱对设备的依赖
        self.emg_recorder = EMGRecoder(emg_parm, ctrparm, pak_length=256)
        self.eeg_recorder = Neuracle(time_buffer=self.t_len)
        self.et_recorder = EyeTrackerClient()

        # 初始化肌电信号处理算法
        params_emg = {"class": 5,
                  "drop_out": 0.4,
                  "time_point": 9,
                  "channel": 3,
                  "Nt": 8,
                  "Ns": 16,
                  "path": os.path.join(os.getcwd(), "Lib", "Checkpoint", "NUDTMEG_EMGNet_0119.pth")
        }
        params_eeg, params_et = {}, {}

        self.emg_algorithm = AlgorithmManage("EMGNet", params_emg)
        self.eeg_algorithm = AlgorithmManage("CCA", params_emg)
        self.et_algorithm = AlgorithmManage("SimpleET", params_emg)

        # 定义向机器人系统发送的指令
        self.messsage = None

        # 初始化视频流系统
        self.video_mode.start()

        # 标志是否进入控制程序
        self.control_flag = False

    
    def status_monitor(self):
        cnt = 0
        init_time_stamp = time.time()
        # 实时监测肌电信号的指令，以便后续实现状态机的状态切换
        while not (self.close_flag and self.control_flag):
            # 每0.5s刷新一次显示
            cnt += 1
            if cnt % 100 == 1: 
                logger.info('当前最新手势为:{}, 当前系统的状态为:{}'.format(self.command, self.status))

            # 编写指令模拟器，用于模拟肌电信号的输出
            cur_time = time.time()

            if cur_time - init_time_stamp < 4:  # 前4s为视频流显示状态
                self.command = 0
            elif cur_time - init_time_stamp < 6 and cur_time - init_time_stamp > 4: # 4~6s 进入选择准备状态
                self.command = 1
            elif cur_time - init_time_stamp < 8 and cur_time - init_time_stamp > 6: # 6~8s 进入SSVEP闪烁状态
                self.command = 2
            elif cur_time - init_time_stamp < 10 and cur_time - init_time_stamp > 8: # 8~10s 发送消息
                self.command = 3
            elif cur_time - init_time_stamp > 30: # 结束程序
                self.command = 4

            # 模拟运行时注释
            time.sleep(0.1)

            # 获取最新的一组肌电信号，计算当前指令信息
            x = self.emg_recorder.get_data().reshape(1, 3, 256)
            time.sleep(0.005)
            gesture, pred = self.emg_algorithm.forward_inference(copy.deepcopy(x))
            # 通过指令平滑、更新指令
            self.gesture_queue.update_fixed_size_queue(pred.item())
            self.command = self.gesture_queue.get_the_smooth_command()


            if self.status == 1 and (self.command == 2 or self.command == 0):
                self.ssvep_mode.stim_flag = True
            else:
                self.ssvep_mode.stim_flag = False
            if self.status == 2 and self.command != 2:
                self.ssvep_mode.show_flag = True
            else:
                self.ssvep_mode.show_flag = False
    
    def control_eeg_emg(self):
        self.result = 0
        # 基于脑电信号和肌电信号的机器人精确控制
        self.control_flag = True
        # 编写范式（视频流显示程序）
        init_time = time.time()
        while self.result != 5:
            time_len = time.time() - init_time
            self.video_mode.update()
            # 编写算法解码眼动信号和肌电信号
            if time_len < 2:
                self.result = 0
            elif time_len > 2 and time_len < 4:
                self.result = 1
            elif time_len > 4 and time_len < 8:
                self.result = 2
            elif time_len > 8 and time_len < 12:
                self.result = 3
            elif time_len > 12 and time_len < 18:
                self.result = 4
            elif time_len > 25:
                self.result = 5

            # 消息模拟发送
            message = [1]
            message.append(1)
            message.append(self.result)
            message_string = ','.join(map(str, message))
            self.control_client.sendto(message_string.encode(), ("192.168.1.101", 9999))
            logger.info('消息{}已发送至机器人控制端'.format(message_string))
        self.control_flag = False


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
                # self.et_recorder.send_message()   # 模拟运行时注释
                self.ssvep_mode.start_one_stim(self.t_len)

                x_eeg = self.eeg_recorder.get_data() 
                logger.info('从设备中获取到一个脑电信号样本，数据形状为:{}'.format(x_eeg.shape))
                x_et = np.array(self.et_recorder.receive_message())
                logger.info('从设备中获取到一个眼动信号样本，数据形状为:{}'.format(x_et.shape))
                _, res_eeg = self.eeg_algorithm.forward_inference(copy.deepcopy(x_eeg))
                _, res_et = self.et_algorithm.forward_inference(copy.deepcopy(x_et))

                # 模拟选择区域值在此修改
                res_eeg = 4
                res_et = 4
                # res_et, res_eeg = res_et + 1, res_eeg + 1
                logger.info('眼动推理的结果为:{}'.format(res_et))
                logger.info('脑电推理的结果为:{}'.format(res_eeg))
                self.ssvep_mode.show_result(res_et)
                # 指令预装载
                self.message = "区域--" + str(res_et) + "--已经被选择，0返回视频流画面，1返回重新选择区域"
            if self.status == 1 and self.command == 0:
                self.status = 0
            if self.status == 2 and self.command == 3:
                # 发送结果
                self.ssvep_mode.show_flag = True
                self.ssvep_mode.show_results_tips(self.message)
                logger.info('{}'.format(self.message))
                print(self.message)
                # 通过TCP/IP将结果发送至机器人控制端
                self.messsage_transmit.sendMessage(self.message.encode())
                message = [0]
                message.append(res_et)
                message_string = ','.join(map(str, message))
                self.control_client.sendto(message_string.encode(), ("192.168.1.101", 9999))
                logger.info('消息{}已发送至机器人控制端'.format(message_string))
                time.sleep(5)
                self.control_eeg_emg()
                self.status = 3

            if (self.status == 2 or self.status == 3) and self.command == 4:
                # 退出所有程序
                self.video_mode.close()
                self.close_flag = True
                self.control_flag = True
                self.window.close()

                self.eeg_recorder.clear_buffer()
                self.eeg_recorder.stop()

                self.control_client.close()
                core.quit()
    
