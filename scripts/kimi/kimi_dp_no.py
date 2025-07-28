#SenderCustom_sender-editor
import ast
import json
import logging
import time

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError, IPConfigError

from tool.DpBitBrowser import get_bit_brow
from tool.client import RequestClient
from tool.datautil import code_log_send_error_msg, get_error_info, re_check
from tool.sqlutil import SqlBuilder
acc_platform = 'kimi'
client = RequestClient()
sqler = SqlBuilder(client,acc_platform)
def get_from_llm(module_params):
    #初始化变量
    tab = None
    browser  =None
    account = None
    acc_code = None
    #获取参数
    prompt =  module_params['prompt']
    #获取优先级
    priority = module_params['priority']

    try:
        # 可以加二至退避重试
        account = sqler.get_account()
        if not account or len(account) == 0 or account.get('status') == 0:
            logging.error("没有可用的账号")
            raise AccountAvalError(f"{acc_platform}_没有可用的账号")

        acc_code = account['acc_code']

        priority_accounts = sqler.get_priority_account(acc_code)

        # 获取对应优先级的账号
        targ_account = None
        for account in priority_accounts:
            if account['priority'] == priority:
                targ_account = account
                acc_code = targ_account['acc_code']
                break
        logging.error(f"取到的账号为{acc_code}_{acc_platform}")

        # 获取cookies
        local_storages = targ_account['local_storage']
        # 转换cookies格式
        local_storages = ast.literal_eval(local_storages)

        #获取web_id
        web_id = targ_account['web_id']
        # 获取bit浏览器
        browser = get_bit_brow(web_id)

        tab = browser.new_tab()

        tab.get('https://www.kimi.com/chat')
        for k,v in local_storages.items():
            tab.set.local_storage(k,v)
        tab.get('https://www.kimi.com/chat')

        # 判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete', timeout=15)
        if not result:
            logging.error(f"{acc_platform}_网页加载缓慢,15秒没有加载出来")
            raise PageLoadTimeoutError(f"{acc_platform}_网页加载缓慢,10秒没有加载出来")

        # 查看cookies是否过期
        time.sleep(3)
        user_name_ele = tab('.user-name')
        if user_name_ele:
            if '登录' == user_name_ele.text:
                logging.error('cookies过期')
                result = sqler.update_account_cookies_status(acc_code, 0)
                logging.error(f"{acc_platform}_{acc_code}_更改cookies状态，执行结果为{result}")
                raise CookiesExpiredError(f"{acc_platform}_{acc_code}_cookies过期")
            else:
                logging.error("cookies没有过期,继续执行")



        # 输入搜索框内容
        for i in range(3):
            inputer = tab('.chat-input-editor-container')
            inputer.click()
            inputer.input(prompt)
            time.sleep(3)
            # 点击生成按钮
            gent_btn_ele = tab('.^send-button-container')
            if 'disabled' in gent_btn_ele.attr('class'):
                logging.error("点击按钮不可被点击")
            else:
                gent_btn_ele.click()
            tab.listen.start('https://www.kimi.com/api/chat/.*/segment/scroll',is_regex=True)
            time.sleep(5)

            #循环重试
            start_time = time.time()
            while time.time() - start_time < 180:
                tab.refresh()
                packet = tab.listen.wait(timeout=10)
                if packet:
                    data = packet.response.body
                    if data and data['items']:
                        tail_reply = data['items'][-1]
                        if tail_reply['role'] == 'assistant':
                            if tail_reply.get('error'):
                                logging.error("返回的错误信息：", tail_reply['error'])
                                #点击开启新会话
                                tab('.new-chat-btn').hover().click()
                                continue
                            else:
                                content = data['items'][-1].get('content', None)
                                if content:
                                    return content


                time.sleep(10)
                continue
    except CookiesExpiredError as e:
        logging.error("账号cookies过期")
        result = sqler.update_account_cookies_status(acc_code, 0)
        logging.error(f"账号{acc_code}cookies过期更新状态完毕，执行结果为{result}")
        code_log_send_error_msg(f"账号{acc_code}cookies过期更新状态完毕，执行结果为{result}")
        raise e


    except Exception as e:
        logging.error(f'获取数据失败{e}',exc_info=True)
        code_log_send_error_msg(f'获取数据失败{get_error_info()}')
        raise  e
    finally:
        if tab:
            if tab.states.is_alive:
                tab.close()
                logging.error("关闭了标签页")


        if acc_code:
            result = sqler.update_account(acc_code)
            logging.error(f"账号{acc_code}回滚acc_status状态完毕，执行结果为{result}")
        else:
            logging.error("没有取到账号无需回滚")
if __name__ == '__main__':
    task_params = {
        'platform': 'kimi',  # 所属平台 #本地部署写poxiao或不写
        'module': 'kimi',
        'invoke_method': 'dp',  # 对应module的名称  #本地模型不写为空或None
        'use_skil': 'get_from_llm',  # 对应module的方法
        'input_params': {  # 对应方法参数
            'prompt': '爬取bilibilib官网数据',
            'mode': {
                'online_search': True,
                'long_think': True
            }

        }
    }
    data = get_from_llm(task_params)
    print(data)