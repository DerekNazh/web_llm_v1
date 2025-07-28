# -*- coding: utf-8 -*-
import json
import logging
import time

import requests
from DrissionPage import Chromium, ChromiumOptions
from loguru import logger


from exceptions.excepts import BitBrowserConnectException, UseBitMaxException


class DpBitBrowser:
    def __init__(self, browser_address='http://127.0.0.1:54345'):
        self.browser_url = browser_address
        self.headers = {'Content-Type': 'application/json'}

    def create_browser(self, name='ls_browser', proxy_data=None, use_proxy=False):
        """
         创建或者更新窗口指纹参数 browserFingerPrint如没有特定需求,只需要指定下内核即可
         https://doc2.bitbrowser.cn/jiekou/liu-lan-qi-jie-kou.html 官方文档
        :param name:        浏览器窗口名称
        :param use_proxy:   是否使用代理
        :param proxy_data:  代理账号,端口
                            # proxy_data = {'ip': '119.84.138.250', 'port': '2021'}
        :return:            窗口Id
        """
        json_data = {
            'name': name,  # 窗口名称
            'remark': '',  # 备注
            "browserFingerPrint": {},  # 指纹代理对象
            'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
            'proxyType': 'noproxy',
        }
        if use_proxy:
            json_data.update({
                'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
                # 代理类型  ['noproxy', 'http', 'https', 'socks5', 'ssh']
                'proxyType': 'http',
                'syncTabs': False,  # 是否同步tabs
                'syncCookies': False,  # 是否同步cookies
                'randomFingerprint': True,  # 每次启动均随机指纹
                'host': proxy_data['ip'],  # 代理主机
                'port': proxy_data['port'],  # 代理端口
                'proxyUserName': proxy_data['proxyUserName'],  # 代理账号
                "proxyPassword": proxy_data['proxyPassword'],  # 代理密码
            })
        # 调用bit
        res = requests.post(f'{self.browser_url}/browser/update', data=json.dumps(json_data), headers=self.headers)
        browser_id = res.json()['data']['id']
        logger.info(f'创建了一个新的窗口{name},窗口id:{browser_id}')
        return browser_id

    def get_exist_browser(self):
        json_data = {'page': 0, 'pageSize': 100}
        res = requests.post(f'{self.browser_url}/browser/list', data=json.dumps(json_data), headers=self.headers)
        json_data = res.json().get('data',None)
        if not json_data:
            logging.error(f"连接bit浏览器失败{res.json()}，返回为{json_data}")
            return None

        browser_ids = [r['id'] for r in json_data['list']]
        logger.info(f"已创建的所有浏览器窗口数量为{json_data['totalNum']}")
        return browser_ids

    def open_browser(self, browser_id):
        """
        打开浏览器
        :param browser_id: 浏览器Id
        :return:
        """
        json_data = {'id': browser_id}


        logging.error(f"打开bit浏览器的browser_id:为{browser_id}")

        res = requests.post(f'{self.browser_url}/browser/open', data=json.dumps(json_data), headers=self.headers)
        start_time = time.time()
        while time.time()-start_time<60:
            if res.json().get('data',None):
                logger.info(f"浏览器窗口Id:{browser_id}已打开,打开的地址为:{res.json()['data']}")
                json_data = res.json()['data']
                return json_data['driver'], json_data['http']

            else:
                time.sleep(.3)
                logger.error(f"浏览器窗口Id:{browser_id}打开失败,返回为:{res.json()},执行重试")
                continue


        #超时返回
        return None,None

    def delete_browser(self, browser_id):
        """
        删除浏览器窗口
        :param browser_id:
        :return:
        """
        json_data = {'id': browser_id}
        res = requests.post(f'{self.browser_url}/browser/delete', data=json.dumps(json_data), headers=self.headers)
        logger.info(f'浏览器窗口:{browser_id} 已删除,{res.json()}')

    def close_browser(self, browser_id):
        """
        关闭浏览器窗口
        :param browser_id: 浏览器Id
        :return:
        """
        json_data = {'id': browser_id}
        res = requests.post(f'{self.browser_url}/browser/close', data=json.dumps(json_data), headers=self.headers)
        logger.info(f'浏览器窗口:{browser_id} 已关闭,{res.json()}')

    def update_browser(self, browser_id, fp):
        """
        更新窗口,支持批量更新,ids传入数组,单独更新之传入一个id即可
        :param browser_id:
        :param fp:
        :return:
        """
        json_data = {'ids': browser_id, 'remark': '我是一个备注', 'browserFingerPrint': fp}
        res = requests.post(f'{self.browser_url}/browser/update/partial', data=json.dumps(json_data),
                            headers=self.headers)

        logger.info(f'浏览器窗口Id:{browser_id} 指纹已更新', res.json()['data'])

    def update_proxy(self, browser_ids, json_data):
        """
         更新浏览器代理信息
         :param browser_ids:
         :param json_data:
            - ids:              bit 窗口 web_id
            - ipCheckService:   IP 查询渠道，默认 ip123in，选项 ip-api, luminati，luminati 为 Luminati 专用
            - proxyMethod:      代理方式 2 自定义代理，3 提取 IP，默认 2
            - proxyType:        代理类型，可选http, https, socks5, ssh 默认 noproxy
            - host:             代理主机
            - port:             代理端口
            - proxyUserName:    代理用户名
            - proxyPassword:    代理密码
         :return:
        """

        res = requests.post(f'{self.browser_url}/browser/proxy/update', data=json.dumps(json_data),
                            headers=self.headers)

        logger.info(f'浏览器窗口Id:{browser_ids} 修改代理成功', res.json())

    @staticmethod
    def dp_connect(adr, browser_url):
        """
        连接dp
        :param adr:
        :param browser_url:
        :return:
        """
        co = ChromiumOptions()
        co.set_browser_path(adr)
        # 无痕模式
        co.incognito()


        logging.error(f"检测!!!!!!! browser_url为:{browser_url}")
        co.set_address(browser_url)
        browser = Chromium(co)

        return browser







    def get_browser_detail(self, browser_id):
        """
        :param browser_id:  浏览器Id
        :return:
        """

        # 获取浏览器信息
        res = requests.post(f'{self.browser_url}/browser/detail', data=json.dumps({
            "id": browser_id,
        }), headers=self.headers)

        # 检查HTTP状态码
        res.raise_for_status()

        try:
            response_data = res.json()
            if not response_data.get('success'):
                logger.error(f"API返回错误: {response_data.get('message')}")
                return None

            json_data = response_data['data']
            # 添加字段访问保护
            proxy_dict = {
                'host': json_data.get('host'),
                'port': json_data.get('port'),
                'proxyUserName': json_data.get('proxyUserName'),
                'proxyPassword': json_data.get('proxyPassword'),
            }
            # 修复原日志中的错误字段（原totalNum应不存在于detail接口）
            logger.info(f"成功获取浏览器详情: {browser_id}")

            return proxy_dict

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"响应解析失败: {str(e)}")
            return None






def get_bit_brow(web_id):

    """
      判断当前启动的比特浏览器中是否存在与此ip对应的窗口，如果有直接新增标签页，如果没有，就找标签页为1的窗口，把此浏览器返回

    """
    dp_browser = DpBitBrowser()
        #打开bit浏览器
    adr1, browser_url = dp_browser.open_browser(web_id)


    logging.error(f'检测！！！！！！adr1:{adr1},browseer_url:{browser_url}')
    # 连接浏览器
    if not adr1 or not browser_url:
        logging.error("比特浏览器连接失败")
        raise BitBrowserConnectException('比特浏览器连接失败')

    logger.info(f'dp待链接地址为: {adr1} browser_url:{browser_url}')
    # # 3. dp 连接窗口
    browser = dp_browser.dp_connect(adr1, browser_url)


    return browser




if __name__ == '__main__':
    # # 构建bit 浏览器
    dp_browser = DpBitBrowser()
    # proxy_data1 = {
    #     'ip': '36.41.68.149',
    #     'port': '1077',
    #     'proxyUserName': '',
    #     'proxyPassword': ''
    # }
    # # 1.创建窗口
    # browser_id1 = dp_browser.create_browser('第一套窗口', proxy_data=proxy_data1, use_proxy=True)
    #
    # # # 2. 打开窗口
    # adr1, browser_url1 = dp_browser.open_browser(browser_id1)
    # logger.info(f'dp待链接地址为: {adr1} browser_url:{browser_url1}')
    # # # 3. dp 连接窗口
    # browser1 = dp_browser.dp_connect(adr1, browser_url1)

    #测试

    #1	49.7.181.56	1090	dhim11n6	xuKiYIgU
    start_time = time.time()
    proxy_info = {
        'host':'49.7.229.21',
        'port':'1007',
        'proxy_user_name':'dhim11n9',
        'proxy_password':'G9JDvaR5'
    }
    browser = get_bit_brow(proxy_info)
    browser.new_tab('http://www.baidu.com')
    print(time.time() - start_time)






