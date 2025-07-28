#semi-input-textarea semi-input-textarea-autosize
#$send-btn-wrapper

#SenderCustom_sender-editor
import json
import logging
import time

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError, IPConfigError

from tool.DpBitBrowser import get_bit_brow
from tool.client import RequestClient
from tool.datautil import *
from tool.sqlutil import SqlBuilder



acc_platform = '豆包'
# 实例化常量
client = RequestClient()
sqler = SqlBuilder(client, acc_platform )


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
        cookies = targ_account['cookie_value']
        # 转换cookies格式
        cookies = format_cookies(cookies, 'list')

        web_id = targ_account['web_id']
        # 获取bit浏览器
        browser = get_bit_brow(web_id)

        tab = browser.new_tab()

        # 设置cookies
        tab.get('https://www.doubao.com/chat')
        for cookie in cookies:
            tab.set.cookies(cookie)
        tab.get('https://www.doubao.com/chat')

        #判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete',timeout=15)
        if not result:
            logging.error(f"{acc_platform}_网页加载缓慢,10秒没有加载出来")
            raise PageLoadTimeoutError(f"{acc_platform}_网页加载缓慢,15秒没有加载出来")

        time.sleep(3)
        #判断cookies失效
        if tab('@@class^emi-button semi-button-primary samantha-button@@text()=登录'):
            result = sqler.update_account_cookies_status(acc_code, 0)
            logging.error(f'更改cookies状态，执行结果为{result}')
            raise  CookiesExpiredError(f'{acc_platform}_{acc_code}_cookies状态过期')




        # 输入搜索框内容
        inputer = tab('.semi-input-textarea semi-input-textarea-autosize')
        inputer.click()
        inputer.input(prompt,clear=True)

        # 点击生成按钮
        gent_btn_ele = tab('.$send-btn-wrapper')
        time.sleep(3)
        gent_btn_ele.child().click(by_js=True)

        #判断是否提示词失效

        time.sleep(3)
        result = False
        start_time = time.time()
        while start_time - time.time() < 240:
            ele = tab.eles('.flex flex-row w-full justify-end')[-1]
            ele2 = ele.after('@@class=semi-button-content-right@@text()=分享')
            if ele2:
                logging.error("生成好")
                result = True
                break
            else:
                logging.error("没有")
                time.sleep(1)
        if not result:
            logging.error("没有正确输入问题")

        tab.listen.start("https://www.doubao.com/alice/message/list?")
        tab.refresh()
        packet = tab.listen.wait(timeout=20)
        data = packet.response.body
        content = data['data']["message_list"][0]["content"]
        content = json.loads(content)['text']
        return content

    except CookiesExpiredError as e:
        logging.error("账号cookies过期")
        result = sqler.update_account_cookies_status(acc_code, 0)
        logging.error(f"账号{acc_code}cookies过期更新状态完毕，执行结果为{result}")
        code_log_send_error_msg(f"账号{acc_code}cookies过期更新状态完毕，执行结果为{result}")
        raise e


    except Exception as e:
        logging.error(f'获取数据失败{get_error_info()}')
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
        'import_path': f'doubao/doubao_dp',
        'prompt': '今天北京多少度'
    }
    data = get_from_llm(task_params)
    print(data)