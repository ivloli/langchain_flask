ERR_OK = 0
ERR_FAIL = -1
ERR_HORBOR = -2
ERR_API_SERVER = -3
ERR_PARAM_INVALID = 1
ERR_NOT_FOUND = 2
ERR_COND_NOT_FULFILLED = 3

errcode_map = {
    ERR_FAIL: '未知错误',
    ERR_PARAM_INVALID: '参数无效',
    ERR_NOT_FOUND: '未找到对象',
    ERR_COND_NOT_FULFILLED: '条件未满足',
}

class BizException(Exception):
    def __init__(self, code=-1, msg=''):
        super().__init__()
        if not msg:
            msg = errcode_map.get(code, '')
        self.args = [code, msg]

    def __str__(self):
        return f'{self.args[0]}：{self.args[1]}'

def check_cond(cond, errcode, errmsg):
    if not cond: raise BizException(errcode, errmsg)