import logging

import requests
import json

from exceptions.excepts import AccountAvalError
from tool.client import RequestClient
from tool.datautil import format_cookies, get_error_info, code_log_send_error_msg
from tool.sqlutil import SqlBuilder
acc_platform = "元宝"
# 配置请求参数
client = RequestClient()
sqler = SqlBuilder(client,acc_platform)
def get_from_llm(module_params:dict):
    # 初始化变量
    tab = None
    browser  =None
    account = None
    acc_code = None
    prompt = module_params['prompt']


    try:
        account = sqler.get_account()
        if not account or len(account) == 0 or account.get('status') == 0:
            logging.error("没有可用的账号")
            raise AccountAvalError("没有可用的账号")
        acc_code = account['acc_code']
        # 获取cookies
        cookies = account['cookie_value']
        # 转换cookies格式
        cookies = format_cookies(cookies, 'str')






        url = "https://ml-platform-api.console.volcengine.com/ark/bff/api/cn-beijing/2024/PullExperienceMessage"
        headers = {
            "Host": "ml-platform-api.console.volcengine.com",
            "Origin": "https://console.volcengine.com",
            "Referer": "https://console.volcengine.com/",
            "User-module": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
            "Content-Type": "text/event-stream",
            "x-csrf-token": "a6842b14b0ef6048c65d306c7cece306",  # 需要替换为实际token
            "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "cookie":cookies
        }


        payload = {
            "SessionId": "exs-202507090948-[Z3Gj5F7RvE-_P-ceGmLRX]",
            "Type": "external",
            "MessageList": [
                {
                    "Sid": "exms-202507091448-[gjPddtBEpf-hboTqwP5ZN]",
                    "SessionId": "exs-202507090948-[Z3Gj5F7RvE-_P-ceGmLRX]",
                    "ParentMessageId": "exms-202507091025-[dVKsU_uwaIZVMt9lqXVoi]",
                    "ContentType": "text",
                    "Content": prompt,
                    "MediaAttachments": {
                        "TosVideo": [],
                        "TosImage": [],
                        "TosDocument": [],
                        "Link": []
                    },
                    "AuthorRole": "user",
                    "ChildMessageIds": [
                        "exms-202507091448-[rM-xI8kHlFEoJM92PBQXC]"
                    ],
                    "ErrorCode": ""
                },
                {
                    "Sid": "exms-202507091448-[rM-xI8kHlFEoJM92PBQXC]",
                    "SessionId": "exs-202507090948-[Z3Gj5F7RvE-_P-ceGmLRX]",
                    "ParentMessageId": "exms-202507091448-[gjPddtBEpf-hboTqwP5ZN]",
                    "ContentType": "text",
                    "Content": "",
                    "DeleteTime": 1,
                    "AuthorRole": "assistant",
                    "ErrorCode": ""
                }
            ],
            "ContextId": 0,
            "UserSetting": [],
            "Rebuild": False,
            "UseBot": False,
            "UseKnowledge": False,
            "EndpointId": "",
            "IsVlm": False
        }

        # 发送请求
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True  # 重要！用于处理服务器推送事件
            )

            # 处理服务器推送事件
            buffer=''
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        #指定标识返回
                        if decoded_line.startswith('data:'):
                            if '"FinishReason":"stop"' in decoded_line:
                                return buffer

                            #增量追加文本
                            data_str = decoded_line[5:].strip()
                            try:
                                data_json = json.loads(data_str)
                            except json.decoder.JSONDecodeError:
                                logging.error(f"非json格式字符串，无法转换类型{data_str}")
                                continue
                            content = data_json['choices'][0]['delta']['content']
                            buffer +=content

                        # 这里可以解析具体的SSE事件数据
            else:
                print(f"请求失败，状态码: {response.status_code}")
                print(response.text)


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
    module_params = {
        'platform': 'huoshan',  # 所属平台 #本地部署写poxiao或不写
        'module': 'hunyuan',
        'invoke_method': 'dp',  # 对应module的名称  #本地模型不写为空或None
        'use_skil': 'get_from_llm',  # 对应module的方法
        'input_params': {  # 对应方法参数
            'prompt': '我是美少女',
            'mode': {
                'online_search': True,
                'long_think': True
            }

        }
    }
    data = get_from_llm(module_params)
    logging.error(data)