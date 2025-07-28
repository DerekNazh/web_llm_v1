import ast
import logging
import time


from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError
from tool.DpBitBrowser import get_bit_brow

from tool.client import RequestClient
from tool.datautil import get_error_info, code_log_send_error_msg, re_check
from tool.sqlutil import SqlBuilder

acc_platform = '问小白'
client = RequestClient()
sqler = SqlBuilder(client,acc_platform)
def get_from_llm(module_params):
    # 初始化变量
    tab = None
    browser = None
    account = None
    acc_code = None
    # 获取参数
    prompt = module_params['prompt']
    # 获取优先级
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
                break

        # 获取cookies
        authorzation = targ_account['cookie_value']


        web_id = targ_account['web_id']
        # 获取代理ip配置
        proxy_ip = targ_account['proxy_ip']

        proxy_ip_info = sqler.get_proxy_info(proxy_ip)
        if not proxy_ip_info or len(proxy_ip_info) == 0:
            logging.error(f"代理ip有误")
            return
        proxy_ip_info = proxy_ip_info[0]

        # 获取bit浏览器
        browser = get_bit_brow(proxy_ip_info)

        tab = browser.new_tab()
        # 设置cookies
        tab.get('https://xiaoyi.huawei.com/chat/')
        for cookie in cookies:
            tab.set.cookies(cookie)
        tab.get('https://xiaoyi.huawei.com/chat/')

        #只能通过认证登录
        handers = {
            'x-yuanshi-authorization':authorzation
        }
        tab.get('https://www.wenxiaobai.com/')
        tab.set.headers(handers)




        #判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete',timeout=15)
        if not result:
            logging.error("网页加载缓慢,10秒没有加载出来")
            raise PageLoadTimeoutError("网页加载缓慢,10秒没有加载出来")


        #判断cookies是否过期


        # 输入搜索框内容
        inputer = tab('.:MsgInput_input_textarea')
        inputer.click()
        inputer.input(prompt)

        # 点击生成按钮
        gent_btn_ele = tab('.^MsgInput_icon_container')
        if 'disabled' not in gent_btn_ele.attr('class'):
            logging.error("可以点击生成按钮")
            gent_btn_ele.click()
        else:
            logging.error("生成按钮不可点击")

        time.sleep(100)

        return tab('.^ChatContent_chat_content_scroller')('.infinite-scroll-component ').children()[0].text


    except CookiesExpiredError as e:
        logging.error("账号cookies过期")
        result = sqler.update_account_cookies_status(acc_code, 0)
        logging.error(f"账号{acc_code}cookies过期更新状态完毕，执行结果为{result}")
        code_log_send_error_msg(f"账号{acc_code}cookies过期更新状态完毕，执行结果为{result}")
        raise e



    except Exception as e:
        logging.error(f'获取数据失败{e}')
        code_log_send_error_msg(f'获取数据失败{get_error_info()}')
        raise e
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
        'platform': 'wenxiaobai',  # 所属平台 #本地部署写poxiao或不写
        'module': 'wenxiaobai',
        'invoke_method': 'dp',  # 对应module的名称  #本地模型不写为空或None
        'use_skil': 'get_from_llm',  # 对应module的方法
        'input_params': {  # 对应方法参数
            'prompt': '你好',
            'mode': {
                'online_search': True,
                'long_think': True
            }

        }
    }
    result = get_from_llm(task_params)
    print(result)


        # print(packet['response']['data']['choices'][0]['delta']['content'])
