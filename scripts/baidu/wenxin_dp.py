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

        tab.get('https://yiyan.baidu.com/X1')
        # 设置cookies
        for cookie in cookies:
            tab.set.cookies(cookie)
        tab.get('https://yiyan.baidu.com/X1')



        #判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete',timeout=15)
        if not result:
            logging.error("网页加载缓慢,10秒没有加载出来")
            raise PageLoadTimeoutError("网页加载缓慢,15秒没有加载出来")

        #查看cookies是否过期

        time.sleep(3)
        if tab('@@class:LoginBtn@@text()=登录'):
            logging.error("cookies过期")
            raise CookiesExpiredError(f"{acc_platform}_{acc_code}_cookies过期")







        # 取消使用联网搜搜，工具
        footBar = tab('.^footBar_')
        online_ele = footBar('@@class^item_@@text()=联网搜索')
        if online_ele:
            if 'active' in online_ele.attr('class'):
                online_ele.click()
                logging.error("关闭联网搜搜")
            else:
                logging.error("联网搜索已经被关闭")
        else:
            logging.error("没有找到使用工具按钮")

        #输入提示词
        start_time = time.time()
        inputer = tab('.yc-editor-paragraph')
        if inputer:
            while time.time() -start_time < 60:
                inputer.click()
                inputer.input( prompt, clear=True)
                time.sleep(2)
                if inputer.text == prompt:
                    logging.error('输入框正常输入')
                    break
                else:
                    time.sleep(.5)
            else:
                logging.error("输入框输入失败")
                return



        # 点击生成按钮
        gent_btn_ele = tab('#sendBtn')
        gent_btn_ele.hover().click()
        time.sleep(3)


        #判断是否发送成功
        convarsation = None
        start_time=time.time()
        while time.time()-start_time < 15:
            convarsation = tab(f'@@class^questionText@@text()={prompt}')
            if convarsation:
                logging.error("点击生成按钮成功")
                break
            time.sleep(.5)
        if not convarsation:
            logging.error("没有点击生成按钮，元素找不到")
            return



       #获取ai回复内容
        start_time = time.time()
        while time.time() - start_time < 300:
            if tab('.^retryBtn_'):
                logging.error("加载数据完毕")
                content = tab.eles('.custom-html md-stream-desktop')[-1].text
                return content
            else:
                logging.error("没有加载数据")
                time.sleep(3)

        else:
            raise Exception(f"{acc_platform}_获取文本超时300s")

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
        'import_path': f'wen/baidu_search_dp',
        'prompt': '今天北京多少度',
        'priority': 1
    }
    data = get_from_llm(task_params)
    print(data)