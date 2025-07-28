import logging
import time

from tool.client import RequestClient

fengkong_count_json={
    '百度搜索': 10,
    '当贝': 10,
    '华为小艺': 10,
    '智谱清言': 10,
    '阶跃': 10,
    '纳米': 10,
    '豆包': 10,
    '火山引擎': 10,
    '元宝': 10,
    '通义千问': 10,
    '文心一言': 10,
    '问小白': 10,
    'deepseek': 10,
    'kimi': 10
}


client = RequestClient()
class SqlBuilder(object):

    def update_max_count(self,platform,max_count):
        result = client.post('poxiao_crm/account_info/update',json={'max_count':max_count},params={'acc_platform':platform}).json()['data']
        return result

def update_interval():
    sql_builder = SqlBuilder()
    start_time = time.time()
    while  True:
        if time.time()-start_time > 3600:
            try:

                for platform,max_count in fengkong_count_json.items():
                    try:
                        result = sql_builder.update_max_count(platform,max_count)
                        logging.error(f"{platform}_{max_count}更改次数的执行结果为{result}")
                    except Exception as e:
                        logging.error(f"{platform}_{max_count}更改次数的执行结果报错为{str(e)}")
                        time.sleep(60)
                        continue
            finally:
                start_time =time.time()
        else:
            time.sleep(60)

if __name__ == '__main__':
 pass