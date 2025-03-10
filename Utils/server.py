'''
Author: Tammie li
Date: 2021-10-27 12:45:20
Description: 定义服务器类
FilePath: \python-sockets\server.py
'''

import socket


class TcpServer:
    def __init__(self, port, size):
        self.port = port
        self.bufferSize = size
        self.server = None
        self.connect = None
        self.connectStatusFlag = False
        self.buffer = None

    def initSocket(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("", self.port))
        self.server.listen(1)                                                                       
        self.server.setblocking(False)
        print("RSVP 服务端初始化就绪！")
        print("Waiting for connection....")

    def waitConnect(self):

        self.connect, addr = self.server.accept()

        print('Connection established at ip:{}, port:{}'.format(addr[0], self.port))
        print("--"*5)
        print("Waiting for client requirements...")
        # self.connect.setblocking(0)

    def sendMessageToClient(self, message):
        if(self.connectStatusFlag):
            self.connect.send(bytes(message, encoding='utf-8'))
            print(message, "消息已发送！")

    def receiveMessageFromClient(self):
        receiveMessage = None
        while(receiveMessage != "close"):
            if(self.connectStatusFlag):
                try:
                    data = self.connect.recv(self.bufferSize)
                    receiveMessage = data.decode()
                    self.buffer = receiveMessage
                    print(receiveMessage)
                except:
                    receiveMessage = None
        self.closeTcpServer()

    def closeTcpServer(self):
        self.server.close()
        self.connect.close()
        print("客户端已关闭，连接断开")



if __name__ == "__main__":
    tcp = TcpServer(2345, 1024)
    tcp.initSocket()

    while(tcp.connectStatusFlag==False):
        try:
            tcp.waitConnect()
            # socket连接成功
            tcp.connectStatusFlag = True
        except:
            pass
    tcp.receiveMessageFromClient()





