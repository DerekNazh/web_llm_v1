#SenderCustom_sender-editor
import logging
import time

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError, IPConfigError

from tool.DpBitBrowser import get_bit_brow
from tool.client import RequestClient
from tool.datautil import get_error_info, code_log_send_error_msg, format_cookies, re_check
from tool.sqlutil import SqlBuilder
acc_platform = '阶跃'
client = RequestClient()
sqler = SqlBuilder(client, acc_platform)
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
        tab.get('https://www.stepfun.com/chats/new')
        for cookie in cookies:
            tab.set.cookies(cookie)
        tab.get('https://www.stepfun.com/chats/new')

        # 判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete', timeout=15)
        if not result:
            logging.error("网页加载缓慢,10秒没有加载出来")
            raise PageLoadTimeoutError("网页加载缓慢,10秒没有加载出来")








        #判断cookies是否过期   user-entry_text
        user_name_ele = tab('.^user-entry_text')
        if user_name_ele:
            if '登录' in user_name_ele.text:
                logging.error('cookies过期')
                result = sqler.update_account_cookies_status(acc_code, 0)
                logging.error(f"更改cookies状态，执行结果为{result}")
                raise CookiesExpiredError("cookies过期")
            else:
                logging.error(f"{acc_platform}_{acc_code}_cookies没有过期,继续执行")







        #点击推理模型
        success = False
        start_time = time.time()
        tuili_ele = tab('.^inline-flex items-center justify-center whitespace-nowrap')
        while time.time() - start_time < 60:
            # 直接判断是否是选中状态，没有选中就点击
            if tuili_ele:
                if 'hover:bg-fill-blue' in tuili_ele.attr('class'):
                    logging.error('当前为选中状态，无效点击')
                    success = True
                    break
                else:
                    tuili_ele.click()

                if 'hover:bg-fill-blue' in tuili_ele.attr('class'):
                    success = True
                    logging.error("点击成功")
                    break
                else:
                    logging.info("点击失败")
                    time.sleep(.3)
                    continue
        if not success:
            logging.error("推理模型点击失败")

        # 取消联网搜搜
        success = False
        start_time = time.time()
        while time.time() - start_time < 30:
            shrink = tab('.$text-sm flex-shrink-0')
            shrink.click()
            if shrink:
                check_area_ele = shrink.after('在整个互联网搜索')
                if check_area_ele:
                    logging.error("点击成功")
                    break
                else:
                    logging.error("点击失败")
                    time.sleep(.3)
        else:
            logging.error("没有点击成功联网列表")
            raise  Exception("没有点击成功联网列表")

        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                online_ele = tab(
                    '@@class=text-sm text-content-primary flex items-center gap-1@@text()=在整个互联网搜索')
                check_area_ele = online_ele.after('t:button@class^peer inline-flex')
                if check_area_ele.attr('aria-checked') == 'true':
                    logging.error("选中联网搜索，开始执行取消")
                    check_area_ele.click(by_js=True)
                    break
                else:
                    logging.error("没有选中联网搜索，无需执行取消")
                    break
            except Exception as e:
                logging.error(f"取消联网搜索失败,{e}")
            finally:
                logging.error("点击其他地方取消联网搜索列表")
                shrink = tab('.$text-sm flex-shrink-0')
                shrink.click()

        else:
            logging.error("取消联网搜索失败")

        # 输入搜索框内容

        start_time = time.time()
        while time.time() - start_time < 60:
            inputer = tab.ele('.^Publisher_textarea')
            if inputer:
                inputer.hover().click()
                inputer.input(prompt, clear=True)

                time.sleep(.3)
                if inputer.text == prompt:
                    logging.error("输入框输入成功")
                    break
                else:
                    logging.error("输入框输入失败")
                    time.sleep(.3)
        else:
            logging.error("输入框输入失败")
            raise Exception("输入框输入失败") #后面需要爆出元素异常(内部)

        # 点击生成按钮
        while time.time() - start_time < 30:
            gent_btn_ele = tab('.custom-icon shrink-0 custom-icon-send-outline')

            gent_btn_ele.child().click()
            time.sleep(1)
            extra_info_ele = tab(f'@@class$whitespace-break-spaces break-words break-all@@text()={prompt}')
            if extra_info_ele:
                logging.error("发送按钮带点击成功")
                break
            time.sleep(.3)
        else:
            logging.error("发送按钮点击失败")
            raise  Exception('发送按钮点击失败')

        start_time = time.time()
        while time.time() - start_time < 300:
            extra_info_ele = tab(f'@@class$whitespace-break-spaces break-words break-all@@text()={prompt}')
            if extra_info_ele.before('.flex gap-1 -ml-2 items-center'):
                markdown_eles = tab('#contentContainer').eles('.^message-markdown_markdown')
                for markdown_ele in markdown_eles:
                    if not 'reason-render' in markdown_ele.attr('class'):
                        logging.info('捕获到llm回答')
                        return markdown_ele.text
            else:
                logging.info("没有值")
                time.sleep(.5)
        else:
            logging.error("没有捕获到llm回答,超时")
            raise Exception('捕获llm回答超时,300s')


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

            # 回滚账号
        if acc_code:
            result = sqler.update_account(acc_code)
            logging.error(f"账号{acc_code}回滚acc_status状态完毕，执行结果为{result}")
        else:
            logging.error("没有取到账号无需回滚")
if __name__ == '__main__':
    task_params = {
        'import_path': f'stepfun/stepfun_dp',
        'prompt': '今天北京多少度',
        'priority':1
    }
    data = get_from_llm(task_params)
    print(data)