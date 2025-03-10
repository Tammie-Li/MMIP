import cv2
import numpy as np
import socket
import struct


# 打开摄像头
cap = cv2.VideoCapture(0)

cap.set(3, 1920)
cap.set(4, 1080)

# 设置TCP通信相关参数
server_ip = '127.0.0.1'  # 服务器IP地址
server_port = 12345       # 服务器端口号
buffer_size = 4096*8        # 接收缓冲区大小

# 创建TCP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定套接字到本地地址和端口
sock.bind(('0.0.0.0', server_port))

# 开始监听连接
sock.listen(1)

# 等待客户端连接
print("等待客户端连接...")
conn, addr = sock.accept()
print('已连接：', addr)




while True:
    # 读取摄像头图像
    ret, frame = cap.read()

    # 将图像编码为JPEG格式
    _, encoded_img = cv2.imencode('.jpg', frame)

    # 获取图像大小
    img_size = len(encoded_img)

    # 将图像大小打包为4字节的二进制数据
    img_size_data = struct.pack('I', img_size)

    # 发送图像大小数据
    conn.sendall(img_size_data)

    # 发送图像数据
    conn.sendall(encoded_img.tobytes())

    # 检测按键，按下 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 关闭摄像头、连接和套接字
cap.release()
conn.close()
sock.close()