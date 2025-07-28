#chat-input-box
import ast
import json
import logging
import re
import time

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from exceptions.excepts import AccountAvalError, CookiesExpiredError, PageLoadTimeoutError, IPConfigError

from tool.DpBitBrowser import get_bit_brow
from tool.sqlutil import SqlBuilder
from tool.client import RequestClient
from tool.datautil import *


acc_platform = 'deepseek'
#实例化常量
client = RequestClient()
sqler = SqlBuilder(client,acc_platform )



def format_deepseek_text(reply:str)->str:
    def clean_and_format(text):
        # 溢出开头的##
        text = re.sub(r'^## ', '  ', text)
        # 移除结尾的 "FINISHED"
        text = re.sub(r'FINISHED\s*$', '', text)
        # 多余换行
        text = re.sub(r'\n+', '\n', text)
        # 替换多余的破折号和多余的星号
        text = re.sub(r'\*{2,}', '**', text)
        text = re.sub(r'---+', '---', text)

        # 如果某个字符串以 ### 开头，并且前面是换行符，则移除 ###
        text = re.sub(r'\n###', '\n   ', text)

        #去除标题开头的**
        text = re.sub(r' \*\*(.*?)\*\*', r"\1", text)
        return text.strip()

    def extract_and_concatenate(data_list):
        respone_content = False
        text_parts = []
        for line in data_list:
            if line.startswith('data:'):
                try:
                    # 提取 JSON 数据部分
                    json_data = json.loads(line[5:])
                    #跳过思考链
                    if json_data.get('p',None)=='response/content':
                        respone_content = True
                    else:
                        if not  respone_content:
                            continue


                    # 检查是否存在 'v' 字段
                    if 'v' in json_data:
                        v = json_data['v']
                        # 如果 'v' 是字典，进一步检查是否包含 'response' 和 'content'
                        if isinstance(v, dict) and 'response' in v and 'content' in v['response'] :
                            content = v['response']['content']
                            if content:
                                text_parts.append(content)
                        # 如果 'v' 是字符串，直接添加
                        elif isinstance(v, str):
                            text_parts.append(v)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
        return ''.join(text_parts)

    extracted_text = extract_and_concatenate(reply.split('\n'))

    # 清洗并格式化文本
    cleaned_text = clean_and_format(extracted_text)

    return cleaned_text

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
        local_storages =ast.literal_eval(local_storages)

        web_id = targ_account['web_id']
        # 获取bit浏览器
        browser = get_bit_brow(web_id)

        tab = browser.new_tab()

        tab.get('https://chat.deepseek.com/')

        for key, value in local_storages.items():
            tab.set.local_storage(key, value)
        tab.get('https://chat.deepseek.com/')

        # 判断网页是否加载成功
        result = re_check(tab.states.ready_state == 'complete', timeout=15)
        if not result:
            logging.error(f"{acc_platform}_网页加载缓慢,10秒没有加载出来")
            raise PageLoadTimeoutError(f"{acc_platform}_网页加载缓慢,15秒没有加载出来")





        #查看cookies是否过期
        if tab('#chat-input'):
            logging.error("cookies没有失效，请继续执行")
        else:
            if tab('@@class=ds-tab__content@@text()=验证码登录'):
                result = sqler.update_account_cookies_status(acc_code,0)
                logging.error(f'更改cookies状态，执行结果为{result}')
                raise  CookiesExpiredError(f'{acc_platform}_{acc_code}_cookies过期')

        #循环点击R1模型

        start_time= time.time()
        while time.time()-start_time<15:
            #点击R1模型
            R1_ele = tab('.^ds-button ds-button--primary ds-button--filled ds-button--rect ds-button--m')
            if R1_ele:
                style = R1_ele.attr('style')
                if style.startswith('--ds-button-color: #fff;'):
                    R1_ele.click(by_js=True)
                    break
                else:
                    logging.error("无需点击，已经选择R1")

            else:
                logging.error("未找到R1模型")
        else:
            logging.error("点击使用r1模型失败")


        #输入搜索框内容
        success=False
        start_time = time.time()
        while time.time() -start_time<60:
            inputer = tab.ele('#chat-input')
            if inputer:
                inputer.hover().click()
                inputer.input(prompt, clear=True)
                if inputer.text == prompt:
                    logging.error("输入框输入成功")
                    success = True
                    break
                else:
                    logging.error("输入框输入失败")
                    time.sleep(.3)
        if not success:
            logging.error("输入框输入失败")
            return


        tab.listen.start('https://chat.deepseek.com/api/v0/chat/completion')


        #循环点击生成按钮
        success = False
        start_time = time.time()
        btn_ele = tab.ele('t:input').next()
        while time.time() - start_time<60:
            if btn_ele:
                btn_ele.hover().click()
                if not btn_ele('.ds-icon'):
                    success=True
                    logging.error("生成按钮点击成功，继续执行")
                    break
                else:
                    logging.error("生成按钮点击失败,重试")
                    continue
        if not success:
            logging.error("点击生成按钮失败")
            return



        packet = tab.listen.wait(timeout=240)
        if packet:
            data = format_deepseek_text(packet.response.body)
            return data
        else:
            logging.error("没有获取到响应包")

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

        #回滚账号
        if acc_code:
            result1 = sqler.update_account(acc_code)
            logging.error(f"账号{acc_code}回滚acc_status状态完毕，执行结果为{result1}")
        else:
            logging.error("没有取到账号无需回滚")
if __name__ == '__main__':
    task_params = {
        'import_path': f'deepseek/deepseek_R1_dp',
        'prompt': '今天北京多少度',
        'priority': 1
    }

    data = get_from_llm(task_params)
    print(data)