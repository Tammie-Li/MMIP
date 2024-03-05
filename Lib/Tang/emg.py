# coding:utf-8
import os
import numpy as np
from multiprocessing import Event, Queue
import time
import datetime
import re
import serial
from Lib.Tang.shm import CreateShm, EEGTYPE, EEGMAXBYTES, EEGMAXLEN, MAXPOINTS
import time
import math
import threading
from threading import Event
import copy

# 最新协议 2023.07.01
# 包头： AB 55
# 标志符：bit1-bit0: 0-12位ADC 1-16位ADC 2-24位ADC 3-32位ADC bit2:不带/带丢包测试 bit3:不带/带trigger
#        bit5-bit4: srate, 0-250, 1-500, 2-1000, 3-2000, 其他位全0，预留
# packlen 包长度
# 数据序列
# 1字节电量（一般为12位ADC所得数据除4而来）
# [1字节丢包测试] 0-255循环
# [1字节trigger] 0-255
# 1字节校验

class dataPakManager():
    def __init__(self):
        self.paklen = 10
        self.srate = 250
        self.sampl_ecount = 5
        self.recv_paklen = 100
        self.sample_interval = 0
        self.timestamp = time.time()

    def parsePak(self,pak):
        self.paklen = pak[3]
        identifier = pak[2]  # 标志字节
        self.srate = SRATES[(identifier >> 4) & 0x03]  # 250,500,1000,2000
        self.sample_interval = 1.0/self.srate
        self.sample_count = int(self.srate/50.)  # 约定每25ms毫秒左右解析一次包

    def recordNow(self):
        # 依据实际测试结果，蓝牙数据传输有50ms系统延迟
        self.timestamp = time.time()
        return self.timestamp

class ADC24decoder():
    def __init__(self):
        # 兼容TI, 24/32位ADC
        # 下位机发送的不是机器字节顺序，需要调整
        ADS1299_Vref = 4.5  # 内部的参考
        ADS1299_gain = 24
        self.fac_uV_per_count = ADS1299_Vref / float((pow(2, 23) - 1)) / ADS1299_gain * 1000000.
        self.rawdt = np.dtype('int32')
        self.rawdt = self.rawdt.newbyteorder('>')

    def tobuf32(self, buf24):
        if buf24[0] > 127:
            return b'\xff' + buf24[:3]
        else:
            return b'\x00' + buf24[:3]

    def decode(self, payloads):
        tmbuf = [self.tobuf32(payloads[i: i + 3]) for i in range(0, len(payloads), 3)]
        buf = b''.join(tmbuf)
        eeg = np.frombuffer(buf, dtype=self.rawdt).astype(EEGTYPE)*self.fac_uV_per_count
        return eeg


SRATES = [250,500,1000,2000]
ULEN = [2,2,3,4]

class EMGRecoder(threading.Thread):
    def __init__(self, param, ctrprm):
        '''
        param: 字典 {'port':'COM5','baudrate':460800}
        ctrprm:
        '''
        super().__init__()
        # threading.Thread.__init__(self)
        self.setDaemon(True)
        self.shm = CreateShm(master = True)
        self.stopEv = ctrprm['stopEv']
        self.backQue = ctrprm['backQue']
        self.adc24decoder = ADC24decoder()

        self.saveFlg = 0
        self.srate = 0
        self.chs = 0
        self.includeID = 0
        self.includeTri = 0
        self.index = 0
        self.buffer = b''
        self.payloads = b''
        self.timestamps = []
        self.ids = b''
        self.tris = b''
        self.sampleCount = 0
        self.battery = b'\x00'
        self.lsttimeclk = 0
        self.virgin = True
        self.temporal_data = None        

        self.devprocount = 1

        self.pkmgr = dataPakManager()

        # 打开设备
        try:       self.ser = serial.Serial(port=param['port'], baudrate=param['baudrate'])
        except:    self.ser = None

    def release(self):
        # 考虑意外退出
        try:
            self.file.close()
        except:
            pass

        self.shm.info[8] = 0

        if self.ser != None:
            try:       self.ser.close()
            except:    pass

        self.shm.release()
        self.stopEv.clear()

    def run(self):
        if self.ser == None:
            self.release()
            return

        self.shm.info[3] = self.devprocount  # 记录 dev第几次启动

        # 协议测试，获得一些基本参数
        self.buffer = b''
        while not self.stopEv.is_set():
            try:
                buf = self.ser.read(1)
            except:
                self.backQue.put(u"接收器被拔出！")
                break
            flg, pak = self.comtest(buf)
            if flg:
                self.pkmgr.parsePak(pak)  # 拿到一个完整的包
                break

        self.buffer = b''
        self.timestamps = []
        while not self.stopEv.is_set():
            try:
                buf = self.ser.read(self.pkmgr.paklen)  # 每次获取一个包
                self.pkmgr.recordNow()  # 记录时间戳
            except:
                self.backQue.put(u"接收器被拔出！")
                break

            self.unpack(buf, self.pkmgr.timestamp)

        self.release()

    # 协议测试，拿到第一个完整的数据包，得到里面的相关信息
    def comtest(self, buffer):
        self.buffer += buffer
        Len = len(self.buffer)
        indx = 0
        while indx <= Len-4: # 先找包头
            if self.buffer[indx] == 0xAB and self.buffer[indx+1] == 0x55:  # 可能是包头
                packlen = self.buffer[indx+3]
                if indx <= Len - packlen:       # 缓存数据能够容纳完整的包
                    pak = self.buffer[indx:indx+packlen]  # 取出这个包
                    if (sum(pak[:-1]) & 0xff) == pak[-1]: # 校验成功
                        self.buffer = b''
                        return True, pak  # 拿到了一个完整的包
                    else:                                 # 非法包
                        indx += 1
                else:                                     # 数据长度不足以包含一个包
                    break
            else:   # 没有搜索到包头
                indx += 1
        self.buffer = self.buffer[indx:]
        return False, None

    def unpack(self, buffer, *args):
        stamp = args[0]
        self.buffer += buffer      # 拼接到末尾
        Len = len(self.buffer)
        indx = 0
        while indx <= Len-4: # 先找包头
            if self.buffer[indx] == 0xAB and self.buffer[indx+1] == 0x55:  # 可能是包头
                packlen = self.buffer[indx+3]
                if indx <= Len - packlen:       # 缓存数据能够容纳完整的包
                    pak = self.buffer[indx:indx+packlen]  # 取出这个包
                    if (sum(pak[:-1]) & 0xff) == pak[-1]: # 校验成功
                        indx += packlen
                        # 给当前数据包分配时间戳
                        faraway = math.ceil((Len - indx) / packlen)  # 倒数第几个包
                        st = stamp - faraway * self.pkmgr.sample_interval
                        self.parse(pak, st)      # 取出的包都通过parse来预处理
                    else:                       # 非法包
                        indx += 1
                else:                           # 数据长度不足以包含一个包
                    break
            else:   # 没有搜索到包头
                indx += 1
        self.buffer = self.buffer[indx:]
        self.dataarange()  # 整理数据

    def parse(self, pak, stamp):  # 拿到一个新包，进行解析
        self.sampleCount += 1
        identifier = pak[2]               # 标志字节
        self.adctype = identifier & 0x03  # 0,1,2,3 -> 12,16,24,32
        self.includeID = (identifier>>2) & 0x01
        self.includeTri = (identifier>>3) & 0x01
        self.srate = SRATES[(identifier>>4) & 0x03]  # 250,500,1000,2000

        datalen = pak[3] - 6 - self.includeID - self.includeTri
        data = pak[4: 4 + datalen]
        self.chs = int(datalen/ULEN[self.adctype])  # 信号通道数

        self.battery = pak[4+datalen]
        if self.includeID:
            id = pak[5+datalen: 6+datalen]
        else:              id = b''
        if self.includeTri: tri = pak[6+datalen:7+datalen]
        else:              tri = b''

        self.payloads += data
        self.ids += id
        self.tris += tri
        self.timestamps.append(stamp)

    def dataarange(self):
        if self.sampleCount <= 0: return
        clk = time.perf_counter()
        if clk - self.lsttimeclk < 0.05:  return   # 控制50ms左右更新一次

        self.lsttimeclk = clk
        ok = False

        if self.adctype == 2:   # 24位adc
            dataay = self.adc24decoder.decode(self.payloads)
            ok = True

        if self.adctype == 3:   # 32位adc
            self.sampleCount = 0

        if ok:
            # 写入数据参数
            if self.virgin:
                self.shm.info[7] = self.includeTri
                self.shm.info[6] = self.includeID
                self.shm.info[5] = self.chs                 # chs
                self.shm.info[4] = self.srate               # srate
                self.shm.info[1] = 0
                self.shm.info[2] = 0
                self.virgin = False

            # 如果绘图端正在读数据，则这里应当等待
            while self.shm.pinfo[0]:
                time.sleep(0.001)

            # 开始写数据
            dataLen = dataay.size         # 数据序列总长度
            Lid = len(self.ids)
            Ltri = len(self.tris)
            self.index += 1
            curPoint = self.shm.info[1]  # 当前存储序列中末尾点位
            sampleN = self.shm.info[2]   # 当前存储序列中采样点数

            if curPoint + dataLen > EEGMAXLEN:
                curPoint = 0      # 超过了缓存最大长度，强制赋0
                sampleN = 0

            self.shm.eeg[curPoint: curPoint+dataLen] = dataay[:]
            try:
                self.shm.shm_id.buf[sampleN:sampleN+Lid] = self.ids  # 丢包测试id
            except:
                print("存在丢包的情况")
            if self.includeTri:
                self.shm.shm_tri.buf[sampleN:sampleN+Ltri] = self.tris     # trigger

            # 保存数据相关
            if self.saveFlg == 0:
                if self.shm.info[8] == 1:  # 开启保存
                    pth = self.shm.getPath()
                    self.file = open(pth, 'wb')
                    # 依次写入eegtype:1-eeg 2-evt,srate,chs,
                    ay = np.array([1, self.srate, self.chs], dtype=EEGTYPE)
                    self.file.write(ay.tobytes())  # 头信息
                    self.saveFlg = self.shm.info[8]

            else:  #self.saveFlg == 1:
                if self.shm.info[8] == 0:  # 结束保存
                    self.file.close()
                    self.saveFlg = self.shm.info[8]

                else:  # 正常保存
                    ndataay = dataay.reshape(self.sampleCount, self.chs)
                    stamp = np.array([self.timestamps]).transpose()
                    ndataay = np.hstack((ndataay,stamp)).flatten()   # 将时间戳添加到最后一列
                    self.file.write(ndataay.tobytes())
                    self.saveFlg = self.shm.info[8]

            # print(dataay.reshape(self.sampleCount, self.chs))

            if self.temporal_data is None: self.temporal_data = dataay.reshape(self.sampleCount, self.chs)
            else: 
                if (self.temporal_data.shape[0] + self.sampleCount) < 256:
                    self.temporal_data = np.concatenate((self.temporal_data, dataay.reshape(self.sampleCount,self.chs)))
                else:
                    start = self.temporal_data.shape[0] + self.sampleCount - 256
                    self.temporal_data = np.concatenate((self.temporal_data[start: ], dataay.reshape(self.sampleCount, self.chs)))
            self.shm.info[2] = sampleN + self.sampleCount  # sampleN
            self.shm.info[1] = curPoint + dataLen  # datapack length
            self.shm.info[0] = self.index
            self.shm.info[2] = 0
            self.shm.info[1] = 0
            self.shm.info[0] = 0


            self.sampleCount = 0
            self.payloads = b''
            self.timestamps = []
            self.ids = b''
            self.tris = b''

    def get_data(self, time):
        tmp_point = int(time * 512)
        data_len = self.temporal_data.shape[0]
        if data_len < tmp_point:
            print("目前采集数据时间过短,需要再等待...") #  一般不会出现这种情况
            return np.random.randint(tmp_point, 3)
        return self.temporal_data.T

def devicepro(parm, ctrprm):
    am = EMGRecoder(parm, ctrprm)
    am.start()
    # am.get_data()



if __name__ == '__main__':
    parm = {'port':'COM8', 'baudrate':460800}
    ctrparm = {}
    ctrparm['stopEv'] = Event()
    ctrparm['backQue'] = Queue()
    devicepro(parm,ctrparm)
