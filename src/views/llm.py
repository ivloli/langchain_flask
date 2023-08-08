from models import *
from utils import *
from llms import LangChainMOSSWrapper
from langchain.llms.base import LLM
import uuid

# 获取 LLM 列表
def get_llm_list(page_num=1, page_size=10) -> JsonObj:
    q = session.query(LLM)
    count = q.count()
    list_ = q.offset((page_num - 1) * page_size).limit(page_size).all()
    return {
        'total': count,
        'list': list_,
    }

# 创建 LLM 记录
def create_llm(name: str, type_: str, path: str, args: JsonObj=None) -> str:
    args = args or {}
    llm = LLM(
        uid=uuid.uuid4().hex,
        name=name,
        type=type_,
        path=path,
        args = json.dumps(args),
    )
    session.add(llm)
    session.commit()
    return llm.uid

# 删除 LLM 记录
def delete_llm(uid: str):
    check_cond(uid, ERR_PARAM_INVALID, "UID 不能为空")
    llm = session.query(LLM).filter(LLM.uid == uid).first()
    check_cond(llm, ERR_NOT_FOUND, "模型 [uid={uid}] 不存在")
    session.query(LLM).filter(LLM.uid == uid).delete()

# 获取 LLM 的 LangChain 包装
def get_llm(name: str) -> LLM: 
    llm = session.query(LLM).filter(LLM.name==name).first()
    check_cond(llm, ERR_NOT_FOUND, "模型 [name={name}] 不存在")
    if llm.type == LLM_TYPE_MOSS:
        return LangChainMOSSWrapper(llm.path, json.loads(llm.args))
    raise ValueError(f'类型 [{llm.type}] 不存在')
