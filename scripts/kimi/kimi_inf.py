import logging
from json import JSONDecodeError

import requests
import json

url = "https://www.kimi.com/api/chat/d1nhkogu8lde8jqh8eh0/completion/stream"
def get_from_llm(module_params):
    #获取参数
    prompt = module_params['prompt']
    online_search = module_params['online_search']
    deep_reasoning = module_params['deep_reasoning']


    authorization_token = module_params['authorization_token']
    headers = {

        "authorization": f"Bearer {authorization_token}",
        "user-module": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

    }

    payload = {
        "kimiplus_id": "kimi",
        "extend": {
            "sidebar": True
        },
        "model": "kimi",
        "use_search": online_search,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "refs": [],
        "history": [],
        "scene_labels": [],
        "use_semantic_memory": True,
        "use_deep_research": deep_reasoning
    }
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        buffer=''
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    #去除data:前缀，解析json
                    line_json =None
                    if line.startswith('data:'):
                        line = line[5:].strip()
                        line_json = json.loads(line)
                    #判断是否增量完成
                    if  line_json and line_json.get('event') == 'all_done':
                        logging.error("增量缓冲字符串完毕")
                        return buffer
                    #判断是否是
                    content = line_json.get('text',None)
                    if content:
                        buffer += content
                    else:
                        logging.error(f"非文本响应单元:{line_json}")
        else:
            logging.error(f"请求失败，状态码：{response.status_code}")
            logging.error(response.text)
    except ConnectionError as e:
            logging.error(f"连接失败，网络超时{e}")

if __name__ == '__main__':
    authorization_token='eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc1NDY2NjgyMSwiaWF0IjoxNzUyMDc0ODIxLCJqdGkiOiJkMW44a2hlZjJrcTJzNmNxZzJhMCIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJjdTBrbmJwZzZpOHNmdWlqM2lnMCIsInNwYWNlX2lkIjoiY3Uwa25icGc2aThzZnVpajNpZmciLCJhYnN0cmFjdF91c2VyX2lkIjoiY3Uwa25icGc2aThzZnVpajNpZjAiLCJyb2xlcyI6WyJ2aWRlb19nZW5fYWNjZXNzIiwiZl9tdmlwIl0sInNzaWQiOiIxNzMxMzU5MTc4ODMxNzg3Mzk2IiwiZGV2aWNlX2lkIjoiNzUyNTEwMjM5ODQ4Mjc0OTcwOSIsInJlZ2lvbiI6ImNuIn0.eJHDl22D4qGHPtrQx2W_56jVW5eVA7miihrj-J7OUIOMED91-T851_jQCFo1Lp0_Ton-3V2E1w65BDkqRbAZ8Q'
    module_params = {'prompt':'你好',
                    'authorization_token':authorization_token,
                    'online_search':True,
                    'deep_reasoning':True
                    }
    data = get_from_llm(module_params)
    print(data)