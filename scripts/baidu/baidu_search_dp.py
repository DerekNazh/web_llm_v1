#chat-input-box

import logging
import time


from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError, IPConfigError

from tool.DpBitBrowser import get_bit_brow
from tool.sqlutil import SqlBuilder
from tool.client import RequestClient
from tool.datautil import code_log_send_error_msg, get_error_info, format_cookies, re_check
acc_platform = '百度搜索'
#实例化常量
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
        #可以加二至退避重试
        account = sqler.get_account()
        if not account or len(account) == 0 or account.get('status') ==0:
            logging.error("没有可用的账号")
            raise AccountAvalError(f"{acc_platform}_没有可用的账号")


        acc_code = account['acc_code']

        priority_accounts = sqler.get_priority_account(acc_code)

        #获取对应优先级的账号
        targ_account = None
        for account in priority_accounts:
            if account['priority'] == priority:
                targ_account = account
                acc_code = targ_account['acc_code']
                break
        logging.error(f"取到的账号为{acc_code}_{acc_platform}")

        #获取cookies
        cookies = targ_account['cookie_value']
        #转换cookies格式
        cookies = format_cookies(cookies,'list')

        web_id = targ_account['web_id']
        #获取bit浏览器
        browser = get_bit_brow(web_id)

        tab = browser.new_tab()

        tab.get('https://chat.baidu.com/search')
        # 设置cookies
        for cookie in cookies:
            tab.set.cookies(cookie)
        tab.get('https://chat.baidu.com/search')



        #判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete',timeout=15)
        if not result:
            logging.error("网页加载缓慢,10秒没有加载出来")
            raise PageLoadTimeoutError("网页加载缓慢,10秒没有加载出来")

        #查看cookies是否过期

        time.sleep(3)
        if tab('@@class=login-btn@@text()=登录'):
            logging.error("cookies过期")
            raise CookiesExpiredError(f"{acc_platform}_{acc_code}_cookies过期")







        #取消联网搜索
        online_ele = tab('.internet-search-icon')
        if online_ele:
            css_online_ele = tab.eles('.:cs-input-model-button')[-1]
            if css_online_ele:
                if 'inactive' in css_online_ele.attr('class'):
                    logging.error("无需点击联网搜索")

                else:
                    online_ele.click()
                    logging.error("取消联网搜索成功")

        else:
            logging.error("没有找到联网搜索按钮")



        #输入提示词
        success = False
        start_time = time.time()

        #有两种ui,先获取第一种页面的输入框
        inputer = tab('#chat-input-box')
        # 再取第二种页面的输入框
        if not inputer:
            inputer = tab('#ai-input-editor')



        while time.time() -start_time < 60:
            inputer.click()
            inputer.input( prompt, clear=True)
            time.sleep(2)
            if inputer.text == prompt:
                logging.error('输入框正常输入')
                success = True
                break
            else:
                time.sleep(.5)
        if not success:
            logging.error("输入框输入失败")
            return

        time.sleep(5)
        # 点击生成按钮
        gent_btn_ele = tab('.:send-icon')

        if 'active-send-icon' in gent_btn_ele.attr('class'):
            logging.error("可以点击生成按钮")
            gent_btn_ele.click()
        else:
            logging.error("生成按钮不可点击")
            raise Exception(f'{acc_platform}_生成按钮不可点击')
        #判断用户提示词是否已经发送
        start_time = time.time()
        while time.time() - start_time < 10:
            send_msg_ele = tab(f'@@class^question-line-break_@@text()={prompt}')
            if send_msg_ele:
                logging.error("用户提示词发送成功")
                break
            else:
                logging.error("用户提示词发送失败")
                time.sleep(.3)
        else:
            logging.error("用户提示词发送失败,超时")
            raise Exception("用户提示词发送失败,超时")


        #循环获取输出文本
        start_time = time.time()
        while time.time() - start_time < 300:
            if send_msg_ele.after('.cs-answer-hover-menu'):
                logging.error("加载数据完毕")
                content = send_msg_ele.after('.^cosd-markdown cos-space-mt-lg').text
                return content
        else:
            raise Exception(f'{acc_platform}_捕获ai回答超时300s')


    except CookiesExpiredError as e:
        logging.error("账号cookies过期")
        result = sqler.update_account_cookies_status(acc_code,0)
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

        #回滚账号
        if acc_code:
            result = sqler.update_account(acc_code)
            logging.error(f"账号{acc_code}回滚acc_status状态完毕，执行结果为{result}")
        else:
            logging.error("没有取到账号无需回滚")

if __name__ == '__main__':
    task_params = {
        'import_path': f'baidu/baidu_search_dp',
        'prompt': '今天北京多少度',
        'priority': 1
    }
    data = get_from_llm(task_params)
    print(data)