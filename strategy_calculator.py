import logging
import os
import sys

import numpy as np

from module_status_recorder import ModuleStatusRecorder


class StrategyCalculator:
    '''
    作用:
        ①负责在服务启动时，注册所有脚本到策略计算器中
        ②负责计算所有脚本此时的运行状态，通过算法，返回出一个最合适的脚本
    '''

    def __init__(self):
        self.module_recorders = []

    # 获取所有需要注册的脚本，导包路径
    def _get_register_scripts(self):
        #获取项目根路路径



        #动态获取，虚拟机环境不支持
        # root_path = None
        # sys_paths = sys.path
        # for path in sys_paths:
        #     if path.endswith('ai_llm_web'):
        #         print(path)
        #         root_path = path
        #         break
        # root_path = f'{root_path}/scripts'


        root_path = r'D:\work\code\PyCharm 2024.3.3\PythonProject\ai\ai_llm_web\scripts'
        #虚拟机支持
        #root_path = 'D:\ai_server\llm_m1\ai_llm_web\scripts'


        # 递归获取所有.py文件
        pys = []
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.endswith('_dp.py'):
                    path1 = root.split('\\')[-1]
                    path2 = file.replace('.py', '')

                    import_path = f'{path1}/{path2}'

                    pys.append(import_path)
        return pys

    # 注册所有的模型脚本
    def register_module_scripts(self):
        # 获取所有接口脚本
        scripts = self._get_register_scripts()
        for script in scripts:
            # 创建 脚本状态记录器
            module_recorder = ModuleStatusRecorder(script)
            # 将脚本状态记录器添加到 平台状态记录器列表中
            self.module_recorders.append(module_recorder)

        # 所有脚本注册完毕
        logging.error("所有符合规则的脚本注册完毕")
    #获取指定名称的模型状态记录器
    def get_recorder(self, recorder_name: str) -> ModuleStatusRecorder:
        for recorder in self.module_recorders:
            if recorder.recorder_name == recorder_name:
                return recorder
        return None


    #删除指定名称的模型记录器
    def remove_recorder(self, recorder_name: str) -> ModuleStatusRecorder:
        for recorder in self.module_recorders:
            if recorder.recorder_name == recorder_name:
                self.module_recorders.remove(recorder)
                logging.error(f"成功移除{recorder_name}模型状态记录器")
                return recorder
        logging.error(f"未找到名称为{recorder_name}的模型记录器")
        return None




    # 计算最佳调用脚本
    def calculate_invoke(self, alpha=0.7, C=5, prior_success_rate=0.8):
        if not self.module_recorders:
            logging.error("脚本未注册")
            return None
        weights = []
        interfaces = []

        for module_recorder in self.module_recorders:
            # 获取原始数据
            success_rate = module_recorder.success_rate
            avg_time = module_recorder.avg_success_time
            exec_count = len(module_recorder.cur_status_queue)

            # 1. 平滑成功率（贝叶斯平均）
            success_count = success_rate * exec_count
            adjusted_success_rate = (success_count + C * prior_success_rate) / (exec_count + C)

            # 2. 计算权重
            w_success = adjusted_success_rate
            w_speed = 1 / (avg_time + 1e-6)  # 防止除零
            weight = alpha * w_success + (1 - alpha) * w_speed

            weights.append(weight)
            interfaces.append(module_recorder)

        # 3. 归一化概率
        total_weight = sum(weights)
        if total_weight <= 0:
            return np.random.choice(interfaces)  # 默认随机选择

        probs = [w / total_weight for w in weights]
        return np.random.choice(interfaces, p=probs)

    #获取当前所有已注册的模型状态记录器
    def get_all_recorder(self):
        return self.module_recorders




if __name__ == '__main__':

    sctor =  StrategyCalculator()
    result = sctor.register_module_scripts()

    result = sctor.calculate_invoke()
    print(result.recorder_name)
