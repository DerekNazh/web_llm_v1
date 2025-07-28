#请求id标签


import requests
import json

url = "https://www.stepfun.com/api/agent/capy.agent.v1.AgentService/ChatStream"

headers = {
    "authority": "www.stepfun.com",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "canary": "false",
    "connect-protocol-version": "1",
    "content-type": "application/connect+json",
    "cookie": "i18next=zh; Oasis-Webid=c35bbf9965170e3b81d3c9fd21897c35e71cc839; Oasis-Token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3RpdmF0ZWQiOnRydWUsImFnZSI6NiwiYmFuZWQiOmZhbHNlLCJjcmVhdGVfYXQiOjE3NTIwNTE5MDIsImV4cCI6MTc1MjA1MzcwMiwibW9kZSI6Miwib2FzaXNfaWQiOjIwMTU2NTE0NDIyNzQ0MjY4OCwidmVyc2lvbiI6Mn0.GEmgUJhmX_U2x0GkkrF2A7Inmyx9y8-PnY-QLIR-jlo...eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOjEwMjAwLCJkZXZpY2VfaWQiOiJjMzViYmY5OTY1MTcwZTNiODFkM2M5ZmQyMTg5N2MzNWU3MWNjODM5IiwiZXhwIjoxNzU0NjI0MDUwLCJvYXNpc19pZCI6MjAxNTY1MTQ0MjI3NDQyNjg4LCJvYXNpc19yX2F0IjoxNzM5NTEwMTYzLCJwbGF0Zm9ybSI6IndlYiIsInZlcnNpb24iOjN9.tKeBjVEE2njH2SEN9zKeFtKQMPN1XxpXFzdhD7ynu8U; sidebar_state=false",
    "oasis-appid": "10200",
    "oasis-language": "zh",
    "oasis-platform": "web",
    "origin": "https://www.stepfun.com",
    "priority": "u=1, i",
    "referer": "https://www.stepfun.com/chats/131804813037248512",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    "x-waf-client-type": "fetch_sdk"
}

payload = {
    "message": {
        "chatSessionId": "131804813037248512",
        "content": {
            "userMessage": {
                "qa": {
                    "content": "你是谁？"
                }
            }
        }
    },
    "config": {
        "model": "deepseek-r1",
        "enableReasoning": True,
        "enableSearch": True
    }
}

# 发送POST请求
response = requests.post(
    url,
    headers=headers,
    data=json.dumps(payload),
    stream=True  # 保持流式连接
)

# 处理流式响应
# 处理流式响应
if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                json_data = decoded_line[6:]
                try:
                    data = json.loads(json_data)
                    # 提取并打印content内容
                    if 'choices' in data and data['choices']:
                        content = data['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            print(content, end='', flush=True)
                except json.JSONDecodeError:
                    continue
            else:
                print(decoded_line, end='', flush=True)
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)
