import cv2
import numpy as np
import socket
import struct

# 设置TCP通信相关参数
server_ip = '127.0.0.1'  # 服务器IP地址
server_port = 12345       # 服务器端口号
buffer_size = 4096        # 接收缓冲区大小

# 创建TCP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接到服务器
sock.connect((server_ip, server_port))
print('已连接到服务器')

# 创建窗口显示摄像头图片
cv2.namedWindow('Video', cv2.WINDOW_NORMAL)

while True:
    # 接收图像大小数据
    img_size_data = sock.recv(4)

    # 解析图像大小数据
    img_size = struct.unpack('I', img_size_data)[0]

    # 接收图像数据
    img_data = b''
    while len(img_data) < img_size:
        data = sock.recv(min(buffer_size, img_size - len(img_data)))
        if not data:
            break
        img_data += data

    # 将图像数据解码成图像
    frame = cv2.imdecode(np.frombuffer(img_data, dtype=np.uint8), 1)

    # 显示图像
    cv2.imshow('Video', frame)

    # 检测按键，按下 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 关闭窗口和套接字
cv2.destroyAllWindows()
sock.close()