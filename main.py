# 主程序入口
# 通过图形界面选择进入相应的实验范式
import os, json 
from Paradigm.ParadigmManage import ParadigmManage


paradigm_name = "Gesture"

dev_para = {'port':'COM7',
            'baudrate':460800}
exp_para = {'trial_num': 3,
            'trial_len': 10,
            'frate': 9,                          
            'block_num': 2,
            'force_array': [0, 1, 2, 3, 4]}
alg_para = {"class": 5, 
            "drop_out": 0.4, 
            "time_point": 9, 
            "channel": 3, 
            "Nt": 8, 
            "Ns": 16, 
            "path": os.path.join(os.getcwd(), "Lib", "Checkpoint", "NUDTMEG_EMGNet_0119.pth")}


if __name__ == "__main__":
    # 从json文件中加载默认参数，后续可以通过图形界面根据需要进行修改
    with open('config.json', 'r') as f:
        default_params = json.load(f)
    p_m = ParadigmManage(paradigm_name, default_params)
    p_m.run()
        