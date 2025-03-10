import socket, time

SERVER_IP = '127.0.0.1'  # 服务器 IP 地址
SERVER_PORT = 1234  # 服务器端口
BUFFER_SIZE = 1024

# 函数声明，用于将字符串解析为二维数组
def stringToArray(data_str):
    rows = data_str.strip().split("\n")
    array = [list(map(float, row.split(","))) for row in rows]
    return array

# 创建 UDP 套接字
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(5):
    time.sleep(5)
    # 发送数据到服务器
    data_to_send = b"start"
    clientSocket.sendto(data_to_send, (SERVER_IP, SERVER_PORT))

    # 接收服务器返回的数据
    data_received, server_address = clientSocket.recvfrom(BUFFER_SIZE)
    print("Received from server:", data_received.decode())

    # 将接收到的字符串解析为二维数组
    array_data = stringToArray(data_received.decode())
    print("Decoded array:", array_data)

# 关闭套接字
clientSocket.close()