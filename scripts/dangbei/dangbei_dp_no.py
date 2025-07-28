#SenderCustom_sender-editor
import logging
import time


from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError, IPConfigError

from tool.DpBitBrowser import get_bit_brow
from tool.client import RequestClient
from tool.datautil import code_log_send_error_msg, get_error_info, format_cookies,re_check
from tool.sqlutil import SqlBuilder

acc_platform = '当贝'
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
        cookies = targ_account['cookie_value']
        # 转换cookies格式
        cookies = format_cookies(cookies, 'list')

        web_id = targ_account['web_id']
        # 获取bit浏览器
        browser = get_bit_brow(web_id)

        tab = browser.new_tab()

        #设置cookies
        tab.get('https://ai.dangbei.com/chat')
        for cookie in cookies:
            tab.set.cookies(cookie)
        tab.get('https://ai.dangbei.com/chat')

        # 判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete', timeout=15)
        if not result:
            logging.error("网页加载缓慢,15秒没有加载出来")
            raise PageLoadTimeoutError(f"{acc_platform}_网页加载缓慢,15秒没有加载出来")


        time.sleep(3)
        # 查看cookies是否过期  dbei-btn dbei-btn-primary
        if tab('@@class^dbei-btn dbei-btn-primary dbei-btn-color-primary@@text()=登录'):
            logging.error(f"{acc_platform}_{acc_code}_cookies过期")
            raise CookiesExpiredError(f"{acc_platform}_{acc_code}_cookies过期")

        # 输入搜索框内容
        inputer = tab('.^SenderCustom_sender-editor')
        inputer.click()
        inputer.input(prompt)

        # 点击生成按钮
        gent_btn_ele = tab('.^dbei-btn dbei-btn-circle dbei-btn-primary dbei-btn-color-primary')

        time.sleep(3)
        gent_btn_ele.child().click()
        time.sleep(3)
        #轮询检测
        user_send_msg_ele = tab(f'@@class=flex flex-col gap-12 items-end@@text()${prompt}')
        if user_send_msg_ele:
            start_time = time.time()
            while time.time() - start_time < 300:
                if user_send_msg_ele.after('.h-full dbei-flex dbei-flex-align-center'):
                    logging.error('输出完成')
                    return tab.eles('.^Chat_ai-message-content')[-1].text
                time.sleep(1)
        return None


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

            # 回滚账号
        if acc_code:
            result = sqler.update_account(acc_code)
            logging.error(f"账号{acc_code}回滚acc_status状态完毕，执行结果为{result}")
        else:
            logging.error("没有取到账号无需回滚")
if __name__ == '__main__':
    task_params = {
        'import_path': f'dangbei/dangbei_dp',
        'prompt': '今天北京多少度',
        'priority': 1
    }
    data = get_from_llm(task_params)
    print(data)