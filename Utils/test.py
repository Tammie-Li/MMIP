import cv2
from psychopy import visual, core, event

# 创建一个窗口
win = visual.Window(size=(1920, 1080), fullscr=False, color=(0, 0, 0), units='pix')

# 使用 OpenCV 捕获视频流（在这里，0 是计算机默认的摄像头）
capture = cv2.VideoCapture(0)
# capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
# capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)

# 检查摄像头是否成功打开
if not capture.isOpened():
    print("Error: Could not open video stream.")
    core.quit()

# 持续捕获视频流并显示
while True:
    ret, frame = capture.read()  # 读取当前帧
    if not ret:
        print("Error: Could not read frame from video stream.")
        break
    
    # 将 OpenCV 图像转换为 PsychoPy 格式
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.flip(frame, 0)
    frame = frame / 255
    print(frame)
    # framea = cv2.resize(frame, (1920, 1080))

    print(frame)
    image_texture = visual.ImageStim(win, image=frame)
    
    image_texture.draw()
    win.flip()

    # 当按下按键时退出循环
    if event.getKeys():
        break

# 清理和释放资源
capture.release()
win.close()
core.quit()