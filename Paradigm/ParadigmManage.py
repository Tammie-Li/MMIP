from Paradigm.Noaction import NoActionParadigm
from Paradigm.Gesture import GestureEMGDataRecoder
from Paradigm.gesture_ssvep import GestureSSVEPParadigm
from Paradigm.physics import PhysicsParadigm


class ParadigmManage:
    # 管理所有的范式
    # 根据范式名称，从json中获取需要的参数，并调用相应的范式
    def __init__(self, name, params):
        self.paradigm_name = name

        if self.paradigm_name == "physics":
            self.paradigm = PhysicsParadigm()
        elif self.paradigm_name == "semi-physics":
            self.paradigm = GestureSSVEPParadigm()

    
    def run(self):
        self.paradigm.run()

        