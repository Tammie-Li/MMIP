import socket

class EyeTrackerClient:
    def __init__(self, server_address='127.0.0.1', server_port=1234):
        self.server_address = server_address
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(2)  # 设置接收超时时间为 2 秒
        self.BUFFER_SIZE = 2048

    # 函数声明，用于将字符串解析为二维数组
    def stringToArray(self, data_str):
        rows = data_str.strip().split("\n")
        array = [list(map(float, row.split(","))) for row in rows]
        return array

    def send_message(self):
        try:
            # 发送消息，开始采集2s的数据
            data_to_send = b"start"
            self.sock.sendto(data_to_send, (self.server_address, self.server_port))
            # 接收服务器返回的数据
        except socket.timeout:
            print("接收服务器响应超时！")
        except Exception as e:
            print(f"发送消息失败: {e}")
    
    def receive_message(self):
        data_received, _ = self.sock.recvfrom(self.BUFFER_SIZE)

        # 将接收到的字符串解析为二维数组
        array_data = self.stringToArray(data_received.decode())
        return array_data

    def close(self):
        self.sock.close()


