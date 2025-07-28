from exceptions.base_except.inner_except import InnerException, BitBrowserException
from exceptions.base_except.outer_except import OuterException

#外部异常
#提示词不合法
class PromptFormatError(OuterException):
    def __init__(self,   message: str = None):
        super().__init__(message)



class PageLoadTimeoutError(InnerException):
    """网页加载超时异常"""
    def __init__(self, message: str = None):
        """
        :param url: 加载超时的网页URL
        :param timeout: 超时时间(秒)
        :param message: 自定义错误信息
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message




#内部异常
#当前平台无账号可用
class AccountAvalError(InnerException):
    def __init__(self,message: str = None):
        super().__init__(message)


class CookiesExpiredError(InnerException):
    def __init__(self,message: str = None):
        super().__init__(message)





#比特浏览器连接失败
#比特浏览器打开窗口数最大
class UseBitMaxException(BitBrowserException):
    def __init__(self,message: str = None):
        super().__init__(message)
#比特浏览器连接错误
class BitBrowserConnectException(BitBrowserException):
    def __init__(self,message: str = None):
        super().__init__(message)

#数据库账号ip配置错误
class IPConfigError(OuterException):
    """ip配置有误"""

    def __init__(self, message: str = None):
        """
        :param message: 自定义错误信息
        """
        self.message = message
        super().__init__(self.message)


