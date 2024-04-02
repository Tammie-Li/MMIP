# 图形界面管理类
# 负责图形界面的实时刷新
# 界面1，系统准备工作，数据实时回传采集以及基本参数配置
# 子界面2，有动作实验范式 for 训练
# 子界面3，有动作在线实验验证
# 子界面4，无动作实验范式 for 训练
# 子界面5，无动作在线实验验证
# 子界面6，SSVEP实验范式 for 训练
# 子界面7，SSVEP在线实验验证
# 子界面8，SSVEP实验范式 for 训练
# 子界面9，SSVEP在线实验验证

class GuiManage:
    def __init__(self, params):
        self.current_page = 0   # 记录当前显示的页面
        self.params = params    # 当前的基本参数信息



