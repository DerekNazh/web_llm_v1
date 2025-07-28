from collections import deque
from typing import Deque


class ModuleStatusRecorder(object):

    success_rate = 0.0

    avg_success_time=0.0

    def __init__(self,plat_form,cur_count=100):
        self.recorder_name = plat_form
        #最近100次调用情况
        self.cur_status_queue: Deque[bool] = deque(maxlen=cur_count)

        # 最近100次调用成功的时间窗口
        self.cur_success_times_queue: Deque[float] = deque(maxlen=cur_count)

    def success_record(self,use_time):
        self.cur_status_queue.append(True)

        self.cur_success_times_queue.append(use_time)


        #重新计算成功率与成功平均时间
        self._update_metrics()



    def fail_record(self):
        self.cur_status_queue.append(False)

        self._update_metrics()

    # 重新计算成功率与成功平均时间
    def _update_metrics(self):
        if self.cur_status_queue:
            self.success_rate = sum(self.cur_status_queue) / len(self.cur_status_queue)
        if self.cur_success_times_queue:
            self.avg_success_time = sum(self.cur_success_times_queue) / len(self.cur_success_times_queue)