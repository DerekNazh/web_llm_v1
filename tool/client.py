import logging
from time import sleep

import requests

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局变量 - 基础URL
BASE_URL = 'http://192.168.31.125:9999'


class RequestClient:
    def __init__(self, timeout=60, retries=2, backoff_factor=0.8):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor

    def _handle_request(self, method, *args, **kwargs):
        for attempt in range(self.retries + 1):
            try:
                kwargs['timeout'] = self.timeout
                response = method(*args, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as errh:
                logging.error(f"Http Error: {errh}")
            except requests.exceptions.ConnectionError as errc:
                logging.error(f"Error Connecting: {errc}")
            except requests.exceptions.Timeout as errt:
                logging.error(f"Timeout Error: {errt}")
            except requests.exceptions.RequestException as err:
                logging.error(f"OOps: Something Else {err}")

            if attempt < self.retries:
                wait_time = self.backoff_factor * (2 ** attempt)
                logging.info(f"Retrying in {wait_time} seconds...")
                sleep(wait_time)
            else:
                logging.error("Max retries exceeded.")
                return None

    def post(self, endpoint, data=None,params=None, json=None, data_class=None, headers={'Content-Type': 'application/json'}):
        # 检查 endpoint 是否以 '/' 开头
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
        url = f"{BASE_URL}{endpoint}"
        logging.info(f"Sending POST request to {url}")
        response = self._handle_request(requests.post, url, params = params,data=data, json=json, headers=headers, timeout=self.timeout)

        if response and response.status_code == 200:
            data = response.json()
            if data['message'] != 'success':
                logging.error(f"服务执行出错, 服务错误信息为：{data}")
                return None
            if data['code'] != 1:
                logging.error(f"服务执行出错, 服务错误信息为{data}")
                return None
            data_list = response
            if data_class and isinstance(data_list, list):
                return [data_class(**item) for item in data_list]
            else:
                return data_list
        else:
            logging.error("Failed to retrieve data.")
            return None

    def get(self, endpoint, params=None, headers=None, data_class=None):
        # 检查 endpoint 是否以 '/' 开头
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
        url = f"{BASE_URL}{endpoint}"
        logging.info(f"Sending GET request to {url}")
        response = self._handle_request(requests.get, url, params=params, headers=headers, timeout=self.timeout)

        if response and response.status_code == 200:
            data = response.json()
            if data['message'] != 'success':
                logging.error(f"服务执行出错, 服务错误信息为：{data}")
                return None
            if data['code'] != 1:
                logging.error(f"服务执行出错, 服务错误信息为{data}")
                return None
            data_list = response
            if data_class and isinstance(data_list, list):
                return [data_class(**item) for item in data_list]
            else:
                return data_list
        else:
            logging.error("Failed to retrieve data.")
            return None


# 使用示例
if __name__ == "__main__":
    client = RequestClient(timeout=30)  # 设置超时时间为1000秒
