# coding:utf-8
import numpy as np
import time
import serial
import time
import os
import threading
from threading import Event

gain = np.array([500/238071,500/229444,500/237622,500/231664,500/236310])

PACKLEN = 23
class Device(threading.Thread):
    def __init__(self, param):
        '''
        param: 字典 {'port':'COM5','baudrate':460800}
        ctrprm:
        '''
        self.param = param
        self.ser = None
        self.stpEv = Event()
        self.stpEv.clear()
        self.weight = np.zeros(5,dtype=np.float64)
        self.tweight = np.zeros(6,dtype=np.float64)
        self.twbuffer = self.tweight.tobytes()
        super().__init__()
        self.setDaemon(True)

    def initialize(self):
        try:
            self.ser = serial.Serial(port=self.param['port'], baudrate=self.param['baudrate'])
        except:
            raise IOError('[com error] can not open device!')

        self.count = 0
        self.buffer = b''
        self.data = np.zeros((9,5))

    def run(self):
        self.initialize()
        if self.ser == None:
            return

        while not self.stpEv.is_set():
            try:
                buf = self.ser.read(PACKLEN)
            except:
                break
            self.unpack(buf)
        self.release()

    def stop(self):
        self.stpEv.set()
        for i in range(10):
            if not self.stpEv.is_set():
                break
            time.sleep(0.1)

    def release(self):
        #self.file.close()
        self.ser.close()
        self.stpEv.clear()

    def unpack(self, buffer):
        self.buffer += buffer      # 拼接到末尾
        Len = len(self.buffer)
        indx = 0
        while indx <= Len-2: # 先找包头
            if self.buffer[indx] == 0xAB and self.buffer[indx+1] == 0x55:  # 可能是包头
                if indx <= Len - PACKLEN:       # 缓存数据能够容纳完整的包
                    pak = self.buffer[indx:indx+PACKLEN]  # 取出这个包
                    if (sum(pak[:-1]) & 0xff) == pak[-1]: # 校验成功
                        self.parse(pak)  #取出的包都通过parse来预处理
                        indx += PACKLEN
                    else:                   # 非法包
                        indx += 1
                else:                           # 数据长度不足以包含一个包
                    break
            else:   # 没有搜索到包头
                indx += 1
        self.buffer = self.buffer[indx:]

    def parse(self,pak):  # 拿到一个新包，进行解析,中值滤波且降采样到10Hz
        ay = np.frombuffer(pak[2:-1],dtype=np.int32)
        self.data = np.vstack((self.data,ay))
        self.data = self.data[-9:,:]
        newdata = np.sort(self.data,axis=0)
        self.weight = newdata[4,:]*gain  # 中值滤波，目的是去除异常值

        self.count += 1
        self.count %= 4  # 原始采样率为80Hz,降采样到20Hz
        if self.count == 0:
            timestamp = time.time()
            self.tweight = np.hstack((self.weight,timestamp), dtype=np.float64)
            self.twbuffer = self.tweight.tobytes()
            # self.file.write(self.wbuffer)
            #print("%.1f\t%.1f\t%.1f\t%.1f\t%.1f"%(self.weight[0],self.weight[1],self.weight[2],self.weight[3],self.weight[4]))


if __name__ == '__main__':
    parm = {'port':'COM3','baudrate':115200,'path':r'./data/data.dat'}
    dev = Device(parm)
    dev.start()
    for i in range(100):
        print("%.1f\t%.1f\t%.1f\t%.1f\t%.1f" % (
        dev.weight[0], dev.weight[1], dev.weight[2], dev.weight[3], dev.weight[4]))
        time.sleep(0.1)

    dev.stop()
