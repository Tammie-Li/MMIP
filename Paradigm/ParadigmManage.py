from Paradigm.Noaction import NoActionParadigm
from Paradigm.Gesture import GestureEMGDataRecoder
from Paradigm.gesture_ssvep import GestureSSVEPParadigm


class ParadigmManage:
    # 管理所有的范式
    # 根据范式名称，从json中获取需要的参数，并调用相应的范式
    def __init__(self, name, params):
        self.paradigm_name = name

        if self.paradigm_name == "gesture":
            pass
            # self._gesture_emg_only_paradigm(self.dev_param["EMGRecoder"], self.exp_param["gesture"], self.exp_param["EMGNet"])
        elif self.paradigm_name == "ssvep":
            self.paradigm = GestureSSVEPParadigm()

    
    def run(self):
        self.paradigm.run()

        