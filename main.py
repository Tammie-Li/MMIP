# 主程序入口
# 通过图形界面选择进入相应的实验范式
import os, json 
from Paradigm.ParadigmManage import ParadigmManage



paradigm_name = "ssvep"


if __name__ == "__main__":
    # 从json文件中加载默认参数，后续可以通过图形界面根据需要进行修改
    with open('config.json', 'r') as f:
        default_params = json.load(f)
    p_m = ParadigmManage(paradigm_name, default_params)
    p_m.run()
