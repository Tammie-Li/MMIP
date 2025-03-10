import numpy as np

class SimpleET:
    def __init__(self):
        self.stim_pos = []
        self.stim_radius = 160
        self.stim_num = 40
        for idx in range(self.stim_num):
            # 屏幕最左端 + 左边留白 + 位置
            x_tmp = ((-960 + 105 + (self.stim_radius + 30) * (idx % 10)) + 1280) / 2560
            y_tmp = 1 - ((540 - 280 - (self.stim_radius + 70) * (idx // 10)) + 720) / 1440
            self.stim_pos.append([x_tmp, y_tmp])

    def _calculate_eu_distance(self, x_real, x_et):
        pos_sum = 0
        cal_sum = 0
        # x_real 为刺激中心点的坐标，x_et 为眼动采集设备返回的结果
        for i in range(x_et.shape[0]):
            # 最后一位为1，表示用户的眼睛不在屏幕范围内
            if int(x_et[i][2]) == 1: continue
            else:
                cal_sum += 1
                pos_sum += np.linalg.norm(x_real - x_et[i][:2])
        if cal_sum == 0: return 20
        return pos_sum / cal_sum

    def recognize(self, x):
        distance = 100
        result = 0
        for idx, enum in enumerate(self.stim_pos):
            dist = self._calculate_eu_distance(enum, x)
            if dist < distance:
                distance = dist
                result = idx
        return result
    


