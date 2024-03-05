from Noaction import NoActionParadigm
from Gesture import GestureEMGDataRecoder


class ParadigmManage:
    # 管理所有的范式
    # 根据范式名称，从json中获取需要的参数，并调用相应的范式
    def __init__(self, name, params):
        self.paradigm_name = name

        self.dev_param = params["Device_Params"]
        self.alg_param = params["Algorithm_Params"]
        self.exp_param = params["Paradigm_Params"]

        if self.paradigm_name == "gesture":
            self._gesture_emg_only_paradigm(self.dev_param["EMGRecoder"], self.exp_param["gesture"], self.exp_param["EMGNet"])
        elif self.paradigm_name == "noaction":
            self._noaction_emg_pressure_paradigm()
    
    def _gesture_emg_only_paradigm(self, params_d, params_e, params_a):
        paradigm = GestureEMGDataRecoder(params_d, params_e, params_a)
        paradigm.run()

    def _noaction_emg_pressure_paradigm(self):
        pass
        