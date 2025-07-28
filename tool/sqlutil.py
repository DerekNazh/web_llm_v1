import logging

from tool.client import RequestClient


class SqlBuilder:
    def __init__(self,client,platform):
        self.client = client
        self.platform = platform
    def get_account(self,use_score=0):
        result = self.client.post('/account/query', json={'acc_platform': self.platform, 'used_core': use_score}).json()['data']
        return result
    def update_account(self,acc_code,hav_core=1):
        result = self.client.get('/account/update', params={'acc_code': acc_code, 'hav_core': hav_core}).json()['data']
        return result
    def update_account_cookies_status(self,acc_code,cookie_status):
        result = self.client.post('/poxiao_crm/account_info/update', json={'cookie_status': cookie_status},params={'acc_code':acc_code,'acc_platform':self.platform}).json()['data']
        return result
    def update_cur_count(self,acc_code):
        result = self.client.post('/account/update/max_count', json={'acc_code': acc_code,'acc_platform': self.platform}).json()['data']
        return result

    #获取账号表的手机号，通过手机号关联代理表的数据进行登录
    def get_proxy_info(self,proxy_ip):
        result = self.client.get('/manage_account/proxy_ip/select', params={'host': proxy_ip}).json()['data']
        return result
    #获取所有大测试用
    def get_proxy_infos(self):
        result = self.client.get('/manage_account/proxy_ip/select').json()['data']
        return result

    #优先级选取web_id操作
    def get_priority_account(self,acc_code):
        result = self.client.get('/poxiao_crm/account_info/select',params={'acc_code':acc_code,'acc_platform':self.platform}).json()['data']
        return result



if __name__ == '__main__':
    client = RequestClient()
    sqler = SqlBuilder(client,'百度')
    result = sqler.get_proxy_info('49.7.174.12')
    print(result)