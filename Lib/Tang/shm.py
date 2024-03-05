#coding:utf-8
import sys
if sys.version_info.major >=3 and sys.version_info.minor >= 8:    pass
else:    raise Exception('[BCIs error] Python >=3.8 is required！')
from multiprocessing import shared_memory
import numpy as np
import sys

EEG_SHM_ = "_BCIs_EEG_"
ID_SHM_ = "_BCIs_ID_"
TRI_SHM = "_BCIs_TRI_"
INFO_SHM = "_BCIs_INFOS_"
PINFO_SHM = "_BCIs_PINFOS_"
EEGTYPE = 'float64'      #eeg数据类型统一为float64
INFOTYPE = 'int32'       #infos数据类型
IDTRITYPE = 'uint8'
PTH_SHM_ = "_BCIs_PATH_"

# 一次信息更新设定50个点，按1000Hz,50ms计算。
# 考虑到读取端可能延迟，这里设置10倍冗余长度。
# 当读取端没有及时读走数据时，新数据添加到末尾。
MAXPOINTS = 50*10
EEGMAXLEN = 32*MAXPOINTS   #最多支持32通道
INFOMAXLEN = 128
EEGMAXBYTES = EEGMAXLEN * 4

'''
eeg: float32, 专门用来存放eeg数据
id: uint8, 用来存放丢包测试数据
trigger: uint8, 用来存放trigger
info: int32, 用来存放一些参数,依次为：
      0-ampindex, 
      1-队列有新数据的字节数L
      2-队列中新数据对应的采样点数N: L=N*4*chs
      3-device进程第几次启动
      4-srate
      5-chs
      6-includeID
      7-includeTri
      8-savedata or not
      9-pathLen

plotinfo: uint8
      0-plot进程正在读数据
'''

class BcisError(Exception):
    def __init__(self,err = 'bcis error'):
        Exception.__init__(self,err)

class CreateShm():
    def __init__(self, master = False):
        self.master = master
        self.shm_eeg0 = None
        self.shm_info = None
        self.shm_pinfo = None
        self.shm_id = None
        self.shm_tri = None
        self.shm_pth = None
        self.shms = []
        self.eegdtype = np.dtype(EEGTYPE)
        self.infodtype = np.dtype(INFOTYPE)
        self.idtritype = np.dtype(IDTRITYPE)

        if self.master: #创建
            self.shm_eeg0 = shared_memory.SharedMemory(create=True, size=self.eegdtype.itemsize * EEGMAXLEN,
                                                       name=EEG_SHM_)  # 申请内存
            self.shm_info = shared_memory.SharedMemory(create=True, size=self.infodtype.itemsize * INFOMAXLEN,
                                                       name=INFO_SHM)  # 申请内存
            self.shm_id = shared_memory.SharedMemory(create=True, size=self.idtritype.itemsize * MAXPOINTS,
                                                       name=ID_SHM_)  # 申请内存
            self.shm_tri = shared_memory.SharedMemory(create=True, size=self.idtritype.itemsize * MAXPOINTS,
                                                       name=TRI_SHM)  # 申请内存
            self.shm_pinfo = shared_memory.SharedMemory(create=True, size=8,
                                                      name=PINFO_SHM)  # 申请内存
            self.shm_pth = shared_memory.SharedMemory(create=True, size=512,
                                                      name=PTH_SHM_)  # 申请内存

        else:  #连接
            try:
                self.shm_eeg0 = shared_memory.SharedMemory(name=EEG_SHM_)
                self.shm_info = shared_memory.SharedMemory(name=INFO_SHM)
                self.shm_pinfo = shared_memory.SharedMemory(name=PINFO_SHM)
                self.shm_id = shared_memory.SharedMemory(name=ID_SHM_)
                self.shm_tri = shared_memory.SharedMemory(name=TRI_SHM)
                self.shm_pth = shared_memory.SharedMemory(name=PTH_SHM_)
            except(FileNotFoundError):
                raise BcisError("no shm master!")

        self.shms = [self.shm_eeg0, self.shm_info, self.shm_pinfo, self.shm_id, self.shm_tri, self.shm_pth]
        self._mapAy2Shm()

    def _mapAy2Shm(self):
        self.eeg = np.ndarray((EEGMAXLEN,), dtype=self.eegdtype, buffer=self.shm_eeg0.buf)
        self.info = np.ndarray((INFOMAXLEN,), dtype=self.infodtype, buffer=self.shm_info.buf)
        self.pinfo = np.ndarray((8,), dtype=self.idtritype, buffer=self.shm_pinfo.buf)
        self.id = np.ndarray((MAXPOINTS,), dtype=self.idtritype, buffer=self.shm_id.buf)
        self.tri = np.ndarray((MAXPOINTS,), dtype=self.idtritype, buffer=self.shm_tri.buf)

    def setPath(self,pth):
        pth = pth.encode('utf-8')
        L = len(pth)
        self.info[9] = L
        self.shm_pth.buf[:L] = pth

    def getPath(self):
        L = self.info[9]
        pth = bytearray(self.shm_pth.buf[:L]).decode('utf-8')
        return pth

    def release(self):
        if self.master:
            for sh in self.shms:
                sh.close()
                sh.unlink()
        else:
            for sh in self.shms:
                sh.close()

