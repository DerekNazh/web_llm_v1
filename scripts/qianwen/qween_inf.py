import logging
import uuid

import requests
import json

from tool.client import RequestClient
from tool.datautil import format_cookies, code_log_send_error_msg, get_error_info
from tool.sqlutil import SqlBuilder

# 请求URL - 注意chat_id需要动态生成或从之前的响应中获取
client = RequestClient()
sqler = SqlBuilder(client, '通义千问')
url = "https://api.tongyi.com/dialog/conversation"

def get_from_llm(task_params):
    tab = None
    account = None
    acc_code = None

    prompt = task_params['prompt']
    try:
        account = sqler.get_account()
        if not account or len(account) == 0 or account.get('status') == 0:
            logging.error("没有可用的账号")
            return
        acc_code = account['acc_code']
        # 获取cookies
        cookies = account['cookie_value']
        # 转换cookies格式
        cookies = format_cookies(cookies, 'dict')

        # 获取代理ip
        proxy_ip = account['proxy_ip']
        if not proxy_ip:
            logging.error(f"该账号没有设置代理：{acc_code}")
            return

        proxy_ip_info = sqler.get_proxy_info(proxy_ip)
        if not proxy_ip_info or len(proxy_ip_info) == 0:
            logging.error(f"代理ip有误")
            return
        proxy_ip_info = proxy_ip_info[0]
        host = proxy_ip_info['host']
        port = proxy_ip_info['port']
        username = proxy_ip_info['proxy_user_name']
        password = proxy_ip_info['proxy_password']
        proxies = {
            'http': f'http://{username}:{password}@{host}:{port}',  # http://user123:pass456@192.168.1.100:8080
        }

        headers = {
            "user-module": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
        }

        payload = {
            "model": "",
            "action": "next",
            "mode": "chat",
            "userAction": "chat",
            "requestId": str(uuid.uuid4()),
            "sessionId": "",
            "sessionType": "text_chat",
            "parentMsgId": "",
            "params": {
                "moduleId": "",
                "searchType": "",
                "pptGenerate": False,
                "bizScene": "",
                "bizSceneInfo": {},
                "specifiedModel": "",
                "deepThink": False,
                "deepResearch": False
            },
            "contents": [
                {
                    "content": prompt,
                    "contentType": "text",
                    "role": "user",
                    "ext": {
                        "searchType": "",
                        "pptGenerate": False,
                        "deepThink": False,
                        "deepResearch": False
                    }
                }
            ]
        }
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            data=json.dumps(payload),  # 注意这里使用data而不是json
            stream=True,  # 对于text/event-stream响应很重要
            proxies=proxies
        )

        # 处理响应
        if response.status_code == 200:
            buffer = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data:"):
                        data_str = line_str[5:].strip()  # 去掉 "data:" 前缀
                        if data_str == "[DONE]":
                            logging.error("Stream finished.")
                            return buffer
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            logging.error(f"不合法的json类型为，字符串数据为:{data_str}")
                            continue
                        content = data.get('msg', '')
                        buffer += content

        else:
            logging.error(f"请求失败，状态码: {response.status_code}")
            logging.error(response)
    except Exception as e:
        logging.error(f'获取数据失败{get_error_info()}')
        code_log_send_error_msg(f'获取数据失败{get_error_info()}')
        raise e
    finally:
        if acc_code:
            result = sqler.update_account(acc_code)
            logging.error(f"账号{acc_code}回滚acc_status状态完毕，执行结果为{result}")
        else:
            logging.error("没有取到账号无需回滚")


if __name__ == '__main__':
    task_params = {
        'import_path': f'qianwen/qween_dp',
        'prompt': '今天北京多少度'
    }
    data = get_from_llm(task_params)
    logging.error(data)
