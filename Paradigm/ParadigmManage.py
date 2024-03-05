from Noaction import NoActionParadigm
from Gesture import GestureEMGDataRecoder


class ParadigmManage:
    # 管理所有的范式
    # 根据范式名称，从json中获取需要的参数，并调用相应的范式
    def __init__(self, name):
        self.paradigm_name = name
        