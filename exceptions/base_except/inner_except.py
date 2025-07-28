class InnerException(Exception):
    """网页加载超时异常"""
    def __init__(self,  message: str = None):
        """
        :param timeout: 时间(秒)
        :param message: 自定义错误信息
        """
        self.message = message
        super().__init__(self.message)

class BitBrowserException(InnerException):
    """比特浏览器连接失败"""
    def __init__(self, message: str = None):
        """
        :param message: 自定义错误信息
        """
        self.message = message
        super().__init__(self.message)
