import cv2
import numpy as np
import math

pi = math.pi
location = ['xian','beijing','shanghai','guangzhou','shenzhen','hefei','baoji','xianyang','tongchuan','chengdu','nanchong','jieshu']

length = 361
width = 260


times = [i * 1 / 60 for i in range(300)]    #时间点，60是屏幕刷新率
freqs = [8 + 0.5*i for i in range(12)] 

# freqs = [1+i for i in range(12)]

phases = [0]
pos = [[ 90*(i//4+1) + width*(i//4) - 30, 20 + 90*(i%4+1) + length*(i%4)]for i in range(12)]
pos = np.array(pos)
def main():
    background = cv2.imread('frame/background/background.png')                    # pic/DiTu.png 

    for frame_num,t in enumerate(times):

        frame = np.zeros_like(background)
        frame = frame + background 

        for i,img_name in enumerate(location):
            img = cv2.imread(f'frame/target/{img_name}.png')
            img = cv2.resize(img,(length,width))

            bright = cos(i,t)

            for c in range(3):
                frame[pos[i][0]:pos[i][0]+width,pos[i][1]:pos[i][1] + length, c] = img[:,:,c] * bright

        cv2.imwrite(f'frame/frame{frame_num+1}.png',frame)

def cos(i,x):
    # f = i // 2          #同一频率有两个目标
    freq = freqs[i]
    # p = i % 2           #目标相位有两种
    # phase = phases[p]
    return (np.cos(freq * 2 * pi * x ) + 1) / 2  #归一化


if __name__ == '__main__':          #走个形式
    main()



