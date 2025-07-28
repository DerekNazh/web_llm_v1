import importlib
import logging
import os.path
import threading
import time

from fastapi import FastAPI
import uvicorn as unicorn
from starlette.responses import JSONResponse

from module_status_recorder import ModuleStatusRecorder
from exceptions.base_except.inner_except import InnerException
from exceptions.base_except.outer_except import OuterException
from other.update_max_count import  update_interval
from strategy_calculator import StrategyCalculator
from tool.datautil import get_local_ip

# 初始化
calculator = StrategyCalculator()
calculator.register_module_scripts()
logging.error(f"脚本注册完成")
app = FastAPI()


def execute(task_params: dict):
    # 获取路径
    import_path = task_params['import_path']

    #获取方法
    # use_skil = task_params['use_skil']
    use_skil = 'get_from_llm'

    #获取
    skil_path = f'scripts/{import_path}/{use_skil}'

    # 分割模块，函数
    path_list = skil_path.split('/')
    import_path = '.'.join(path_list[: -1])
    func_name = path_list[-1]

    # 动态调用
    module = importlib.import_module(import_path)
    try:
        func = getattr(module, func_name)
    except AttributeError as e:
        logging.error('根据路径锁定脚本失败')
        raise OuterException(f'根据路径锁定脚本失败 {e}')




    output = func(task_params)

    return output



@app.post('/poxiaoaibaipiao')
def inf_invoke(params: dict):
    invoke_success = False
    cur_module_recorder:ModuleStatusRecorder =  None
    recorder_name = None
    model = None
    start = time.time()
    try:

        # 获取参数，输入判断
        prompt = params['prompt']
        priority =  params['priority']



        if not prompt:
            logging.exception("提示词无效，请重新请求")
            return {'code':502,'reply':'提示词无效，请重新更改'}


        #策略计算器返回最佳状态模型记录器
        cur_module_recorder = calculator.calculate_invoke()


        recorder_name = cur_module_recorder.recorder_name

        model = os.path.basename(recorder_name).replace('_dp', '')

        task_params = {
            'import_path':recorder_name,
            'prompt':prompt,
            'priority':priority
        }

        output = execute(task_params)
        invoke_success = True


        if output:
            return JSONResponse({
                'code':200,
                'reply':output,
                'model':model,
                'time':time.time() - start,
                'msg':'执行成功!'
            })
        else:
            return JSONResponse({
                'code':500,
                'msg':'执行任务失败，未报错，需查明原因',
                'model': model,
                'time':time.time() - start
            })

    #平台模型内部异常需计算策略记录器
    except InnerException as e:
        #计算策略记录器
        logging.error('需计算策略记录器')
        cur_module_recorder.fail_record()


        return JSONResponse({
            'code': 501,
            'msg': e.message,
            'model':model,
            'time': time.time() - start
        })
    except OuterException as e:
        logging.error("非平台原因结束，无需使用记录器")
        return JSONResponse({
            'code': 502,
            'msg': e.message,
            'model': model,
            'time': time.time() - start
        })


    except Exception as e:
        logging.exception(f"执行任务失败:{e}")
        return JSONResponse({
            'code':503,
            'msg':f'执行任务失败,{e}',
            'model': model,
            'time':time.time()-start
        })
    finally:
        #动态更新接口状态记录器
        if invoke_success:
            calculator.get_recorder(recorder_name).success_record(time.time() - start)
        else:
            calculator.get_recorder(recorder_name).fail_record()

def start_up_ai_server():
    #启动服务

    #开始主要逻辑
    logging.error("-----------开始主要逻辑--------------")
    #开启线程定时更改账号使用次数
    thread = threading.Thread(target=update_interval)
    thread.start()
    #启动http服务
    unicorn.run(app, host=get_local_ip(), port=9811)

    logging.error("-----------服务执行结束--------------")





if __name__ == '__main__':
    start_up_ai_server()