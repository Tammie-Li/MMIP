import cv2
import time

img0 = cv2.imread('000.jpg')

i = 1
while(1):
    time.sleep(0.5)
    img = cv2.imread('000.jpg')



    if cv2.subtract(img0,img).sum()==0:
        # print('0')
        continue
    else:
        cv2.imwrite(f'{i}.jpg',img)
        print('Saved!')
        img0 = img
        i = i + 1