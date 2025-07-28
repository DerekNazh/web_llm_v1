import logging
import os,sys,traceback
import socket
from typing import Union, Dict, List
import time
import requests
from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions



def get_error_info():

    def get_error_details(show_full_path=False):
        """
        获取当前异常的详细信息

        参数:
            show_full_path: bool, 是否显示完整文件路径(默认只显示文件名)

        返回:
            list: 包含每个堆栈帧详细信息的字典列表
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if not all([exc_type, exc_value, exc_traceback]):
            return []

        tb_list = traceback.extract_tb(exc_traceback)
        error_details = []

        for frame in tb_list:
            filename, line_num, func_name, text = frame

            # 处理文件名显示
            file_display = filename if show_full_path else os.path.basename(filename)

            # 构建每个堆栈帧的信息
            frame_info = {
                'file': file_display,
                'line': line_num,
                'function': func_name,
                'code': text.strip() if text else ''
            }
            error_details.append(frame_info)

        return {
            'error_type': exc_type.__name__,
            'error_message': str(exc_value),
            'stack_trace': error_details
        }
    def format_error_info(error_info: dict) -> str:
        """格式化错误信息为易读字符串"""
        error_str = [
            "⚠️ 错误发生 ⚠️",
            f"错误类型: {error_info.get('error_type', 'UnknownError')}",
            f"错误信息: {error_info.get('error_message', 'No error message')}",
            "\n调用堆栈:"
        ]

        for i, frame in enumerate(error_info.get('stack_trace', []), 1):
            error_str.extend([
                f"\n帧 {i}:",
                f"  文件: {os.path.basename(frame.get('file', None))}",
                f"  行号: {frame.get('line', '?')}",
                f"  函数: {frame.get('function', 'Unknown function')}",
                f"  代码: {frame.get('code', 'No code available')}"
            ])

        return "\n".join(error_str)

    error_info = get_error_details()
    formatted_error_info = format_error_info(error_info)
    return formatted_error_info

def code_log_send_error_msg(msg): # 小群
    try:
        url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d02760c9-7bf4-4693-bea9-7c3d6a23f587'
        data = {
            "msgtype": "text",
            "text": {
                "content": msg
            }
        }
        response = requests.post(url=url, json=data)
        return response
    except Exception as e:
        logging.error("企业微信连接失败")
        return None


#cookoies格式转化
def format_cookies(
        cookies: Union[str, Dict[str, str], List[Dict[str, str]]],
        output_format: str = "dict"
) -> Union[str, Dict[str, str], List[Dict[str, str]]]:
    """
    转换 cookies 格式（支持字符串/字典/字典列表互相转换）

    参数:
        cookies: 输入 cookies，可以是:
            - 字符串: "key1=value1; key2=value2"
            - 字典: {"key1": "value1", "key2": "value2"}
            - 字典列表: [{"name": "key1", "value": "value1"}, {"name": "key2", "value": "value2"}]
        output_format: 输出格式，可选:
            - "str": 返回字符串格式（key=value）
            - "dict": 返回字典格式
            - "list": 返回字典列表格式（包含name/value键）

    返回:
        转换后的 cookies 格式

    示例:
        >>> convert_cookies("a=1; b=2", "dict")
        {'a': '1', 'b': '2'}
        >>> convert_cookies([{"name": "a", "value": "1"}], "str")
        'a=1'
    """
    # 首先统一转换为中间格式（字典）
    temp_dict = {}

    if isinstance(cookies, str):
        # 字符串 → 字典
        for pair in cookies.split(';'):
            pair = pair.strip()
            if not pair:
                continue
            if '=' in pair:
                key, value = pair.split('=', 1)
                temp_dict[key.strip()] = value.strip()
            else:
                temp_dict[pair] = ''

    elif isinstance(cookies, dict):
        # 字典 → 保持字典
        temp_dict = cookies

    elif isinstance(cookies, list) and all(isinstance(x, dict) for x in cookies):
        # 字典列表 → 字典
        for item in cookies:
            if 'name' in item and 'value' in item:
                temp_dict[item['name']] = item['value']
    else:
        raise ValueError("不支持的 cookies 格式")

    # 根据要求的格式转换
    if output_format == "dict":
        return temp_dict

    elif output_format == "str":
        return '; '.join(f"{k}={v}" for k, v in temp_dict.items())

    elif output_format == "list":
        return [{"name": k, "value": v} for k, v in temp_dict.items()]

    else:
        raise ValueError(f"不支持的输出格式: {output_format}")



def get_local_ip():
    try:
        # 创建一个 UDP 套接字（不真正发送数据）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 连接 Google DNS
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"获取 IP 失败: {e}"


def re_check_pro(func, condition, timeout=10, interval=0.5, *args, **kwargs):
    """
    重复检查条件并执行函数，直到条件满足或超时

    :param func: 要执行的函数
    :param condition: 检查条件，可以是函数或表达式
    :param timeout: 超时时间（秒）
    :param interval: 检查间隔（秒）
    :param args: 传递给func的位置参数
    :param kwargs: 传递给func的关键字参数
    :return: func的返回值，或超时返回False
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # 检查条件：如果condition是函数则调用，否则直接判断
        if callable(condition):
            cond_result = condition()
        else:
            cond_result = condition

        if cond_result:
            try:
                # 执行目标函数
                result = func(*args, **kwargs)
                if result:  # 如果结果有效则返回
                    return result
            except Exception as e:
                # 可以选择记录异常
                # logging.error(f"Function execution failed: {str(e)}")
                pass

        # 等待下次检查
        time.sleep(interval)

    return False

def re_check(expr,timeout=10,interval=1):

    start_time = time.time()
    while time.time() - start_time < timeout:
        if expr:
            return True
        time.sleep(interval)
    return False


#设置代理
def set_my_proxy(tab=None,proxy=None):

    tab.get('chrome-extension:')

    extension_items = tab("t:extensions-manager").sr("#viewManager")
    extension_items = extension_items.ele("#items-list").sr(".items-container").eles("t:extensions-item")




    tab.get('chrome-extension://kihandlljpjcidpnmgjhidlpiioamglp/popup.html')
    host = proxy['host']
    port = proxy['port']
    username = proxy['proxy_user_name']
    password = proxy['proxy_password']

    tab('#proxyServer').click().input(host,clear=True)
    tab('#proxyPort').click().input(port, clear=True)
    tab('#proxyUsername').click().input(username,clear=True)
    tab('#proxyPassword').click().input(password,clear=True)

    #点击确认
    tab('#enable').hover().click()



    return False



def get_columns_by_dicts(dicts, columns, drop_none=False):
    """
    从字典列表中提取指定列的值，并返回结果为字典列表。

    参数:
        dicts (list of dict): 字典列表。
        columns (list of str): 需要提取的列名列表。
        drop_none (bool): 是否过滤掉包含 None 值的行。默认为 False。

    返回:
        list of dict: 提取的列值组成的字典列表。
    """
    if drop_none:
        # 过滤掉包含 None 值的行
        filtered_dicts = [d for d in dicts if all(d.get(col) is not None for col in columns)]
    else:
        filtered_dicts = dicts

    # 提取指定列并生成结果
    result = [{col: d.get(col) for col in columns} for d in filtered_dicts]

    return result
if __name__ == '__main__':
    result = re_check_pro(lambda :[
        print('aaa'),
        print('bbb')

    ]

    ,True)
    print(result)