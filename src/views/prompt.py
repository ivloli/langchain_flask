from models import *
# from flask import Blueprint
# from flask import request as req
from utils import *
import uuid
from typing import *

# pmt = Blueprint('prompt', __name__, url_prefix='/prompt')

# @pmt.route('/', methos=['GET'])
def get_prompts(page_num=1, page_size=10) ->  JsonObj:
    q = session.query(Prompt)
    total = q.count()
    list_ = q.offset((page_num - 1) * page_size).limit(page_size).all()
    return {
        'total': total,
        'list': list_,
    }

def get_single_prompt(uid: str):
    prt = session.query(Prompt).filter(Prompt.uid==uid).first()
    check_cond(prt, ERR_NOT_FOUND, f"提示词 [uid={uid}] 不存在")
    return prt

'''
def check_prompt_create(data):
    check_cond(data.get('template'), ERR_PARAM_INVALID, '模版参数不能为空')
    if data.get('few_shot'):
'''

# @pmt.route('/', methos=['POST'])
def create_prompt(
    name='', few_shot=False, 
    template='', examples='[]',
    prefix='', suffix='', seperator='\n'
    ) -> str:
    # data = req.json
    t = Prompt(
        uid=uuid.uuid4().hex,
        name=name,
        few_shot=few_shot,
        template=template,
        examples=json.dumps(examples),
        prefix=prefix,
        suffix=suffix,
        seperator=seperator,
    )
    session.add(t)
    session.commit()
    return t.uid

# @pmt.route('/update', methos=['POST'])
def update_prompt(
    uid: str, name='', few_shot=False, 
    template='', examples='[]',
    prefix='', suffix='', seperator='\n'
    ):
    # data = req.json
    t = session.query(Prompt).filter(Prompt.uid==uid).first()
    check_cond(t, ERR_NOT_FOUND, f'提示词 [uid={uid}] 不存在')
    session.query(Prompt).filter(Prompt.uid==uid).update(dict(
        name=name,
        few_shot=few_shot,
        template=template,
        examples=json.dumps(examples),
        prefix=prefix,
        suffix=suffix,
        seperator=seperator,
    ))
    session.commit()
    # return ok()

# @pmt.route('/delete', methos=['GET'])
def delete_prompt(uid: str):
    t = session.query(Prompt).filter(Prompt.uid==uid).first()
    check_cond(t, ERR_NOT_FOUND, f'提示词 [uid={uid}] 不存在')
    session.query(Prompt).filter(Prompt.uid==uid).delete()
    session.commit()
    # return ok()
