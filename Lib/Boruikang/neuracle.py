'''
Coding: utf-8
Author: vector-wlc
Date: 2021-04-28 09:52:21
Description: Neuracle 在线获取数据类
'''

from Lib.Boruikang.dataServer import DataServerThread
import time


class Neuracle:
    def __init__(self, time_buffer=7, hostname='127.0.0.1', port=8712, srate=1000):
        channels = []
        with open("./Lib/Boruikang/chan.txt", "r") as f:
            for line in f.readlines():
                line = line.strip().split("\t")[1]
                channels.append(line)

        # 配置设备
        neuracle = dict(device_name='Neuracle', hostname=hostname, port=port,
                        srate=srate, chanlocs=channels, n_chan=len(channels))

        # 选着设备型号,默认Neuracle
        self.target_device = neuracle
        self.time_buffer = time_buffer
        # 初始化 DataServerThread 线程
        self.thread_data_server = DataServerThread(device=self.target_device['device_name'], n_chan=self.target_device['n_chan'],
                                                   srate=self.target_device['srate'], t_buffer=time_buffer)

    def start(self):
        # 建立TCP/IP连接
        notconnect = self.thread_data_server.connect(
            hostname=self.target_device['hostname'], port=self.target_device['port'])
        if notconnect:
            raise TypeError(
                "Can't connect recorder, Please open the hostport ")
        else:
            # 启动线程
            self.thread_data_server.Daemon = True
            self.thread_data_server.start()
            print('Data server connected')

    def get_data(self):
        # 得到数据
        # time_sec: 得到多长时间的数据
        while True:
            nUpdate = self.thread_data_server.GetDataLenCount()
            if nUpdate > (self.time_buffer * self.target_device['srate'] - 1):
                data = self.thread_data_server.GetBufferData()
                self.thread_data_server.ResetDataLenCount()
                # print(data.sum(axis=1))
                # print(data)
                break
        return data

    def clear_buffer(self):
        self.thread_data_server.ResetDataLenCount()

    def stop(self):
        self.thread_data_server.stop()
