from flask import Flask, request, jsonify, Response, stream_with_context
import helper
import time, json
from langchain.llms import OpenAI
from langchain import LLMChain
from llms.LangChainMOSSWrapper import LangChainMOSSWrapper
from models import DataSet,Prompt,DataItem
from views import dataset, prompt, llm
from jitCl import jitChain
from typing import Dict
import pandas as pd
import os

app = Flask(__name__)

# 定义一个接收 GET 请求的视图函数
@app.route('/hello', methods=['GET'])
def hello():
    name = request.args.get('name', 'Guest')
    return f'Hello, {name}!'

# 定义一个接收 POST 请求的视图函数
@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify(data)

def generate_numbers():
    for i in range(1, 11):
        yield str(i)
        time.sleep(1)

@app.route('/count', methods=['GET'])
def count():
    return Response(stream_with_context(generate_numbers()), content_type='text/plain')

@app.route('/list_prompt', methods=['GET'])
def list_prompt():
    try:
        page_num = int(request.args.get('page_num','1'))
        page_size = int(request.args.get('page_size','10'))
        ps = prompt.get_prompts(page_num, page_size)
        psList = list[Prompt](ps.get("list"))
        displayList = []

        for v in psList:
            examplesDict = None
            if v.few_shot:
                examplesJsonStr = bytes(str(v.examples), 'utf-8').decode('unicode_escape')
                examplesJsonStr = examplesJsonStr.strip('"')
                examplesJsonStr = examplesJsonStr.strip("'")
                if examplesJsonStr.startswith("{") or examplesJsonStr.startswith("["):
                    examplesDict = json.loads(examplesJsonStr)
                if isinstance(examplesDict,dict):
                    examplesDict = [examplesDict]
            vd = {
                    "id": v.id,
                    "examples":examplesDict,
                    "is_few_shot":bool(v.few_shot),
                    "name":str(v.name),
                    "prefix":str(v.prefix),
                    "suffix":str(v.suffix),
                    "seperator":str(v.seperator) or "\n",
                    "template":str(v.template),
                    }
            displayList.append(vd)

        result = {
            "total": ps.get("total"),
            "list": displayList
        }

        return jsonify(result), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400

@app.route('/delete_prompt', methods=['GET'])
def delete_prompt():
    uid = request.args.get('uid','')
    if len(uid) == 0:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    try:
        prompt.delete_prompt(uid)
    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    return jsonify({
        "code":0,
        "msg":"ok"
        }), 200

@app.route('/add_edit_prompt', methods=['POST'])
def add_edit_prompt():
    try:
        inPrompt = request.get_json()
        examples = inPrompt.get("examples")
        if examples is not None:
            if helper.is_list_of_dicts_with_str_keys_and_values(examples) == False:
                return jsonify({"code":-1,"msg": "Invalid input, examples must be a list if provided"}), 400
        prompt.create_prompt(
                name=inPrompt.get("name") or '',
                few_shot=inPrompt.get("is_few_shot") or False,
                examples=examples,
                template=inPrompt.get("template") or '',
                prefix=inPrompt.get("prefix") or '',
                suffix=inPrompt.get("suffix") or '',
                seperator=inPrompt.get("seperator") or '\n',
                )
    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    return jsonify({
        "code":0,
        "msg":"ok"
        }), 200

@app.route('/get_prompt_columns', methods=['get'])
def get_prompt_columns():
    uid = request.args.get('uid','')
    if len(uid) == 0:
        return jsonify({
            "list": ["question"]
            }), 200
    try:
        myPromptModel = prompt.get_single_prompt(uid)
        if myPromptModel is not None:
            if myPromptModel.few_shot:
                examplesDict = None 
                examplesJsonStr = bytes(str(myPromptModel.examples), 'utf-8').decode('unicode_escape')
                examplesJsonStr = examplesJsonStr.strip('"')
                examplesJsonStr = examplesJsonStr.strip("'")
                if examplesJsonStr.startswith("{") or examplesJsonStr.startswith("["):
                    examplesDict = json.loads(examplesJsonStr)
                if isinstance(examplesDict,dict):
                    examplesDict = [examplesDict]
                myTemplate = jitChain.generate_few_prompt_template(examplesDict, myPromptModel.template, myPromptModel.suffix, myPromptModel.prefix or '', myPromptModel.seperator or '\n')
            else:
                myTemplate = jitChain.generate_prompt_template(myPromptModel.template)
        else:
            myTemplate = jitChain.generate_none_prompt_template()
        inColumns = myTemplate.input_variables
        return jsonify({
            "list": inColumns
            }), 200
    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400

@app.route('/list_dataitem', methods=['GET'])
def list_dataitem():
    try:
        page_num = int(request.args.get('page_num','1'))
        page_size = int(request.args.get('page_size','10'))
        dataset_name = request.args.get('dataset_name','')
        if len(dataset_name) == 0:
            return jsonify({"code":-1,"msg": "Invalid input."}), 400
        dset = dataset.get_single_dataset(dataset_name)
        if dset is None:
            return jsonify({"code":-1,"msg": "get dataset failed."}), 500
        duid = str(dset.uid)
        ditems = dataset.get_dataitems(duid, page_num, page_size)
        ditemList = list[DataItem](ditems.get("list"))
        displayList = []
        for v in ditemList:
            argsDict, _ = helper.parse_json(v.args)
            vd = {
                    "id": v.id,
                    "uid": v.uid,
                    "dataset_uid": v.dataset_uid,
                    }
            if argsDict is not None:
                vd["args"] = argsDict
            else:
                vd["args"] = None
            displayList.append(vd)
            #print(vd["args"])

        result = {
            "total": ditems.get("total"),
            "list": displayList
        }
        return jsonify(result), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400

@app.route('/delete_dataitem', methods=['GET'])
def delete_dataitem():
    uid = request.args.get('uid','')
    if len(uid) == 0:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    try:
        dataset.delete_single_dataitem(uid)
    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    return jsonify({
        "code":0,
        "msg":"ok"
        }), 200

@app.route('/list_dataset', methods=['GET'])
def list_dataset():
    try:
        page_num = int(request.args.get('page_num','1'))
        page_size = int(request.args.get('page_size','10'))
        ds = dataset.get_datasets(page_num, page_size)
        dsList = list[DataSet](ds.get("list"))
        displayList = []
        for v in dsList:
            vd = {
                    "id": v.id,
                    "uid": v.uid,
                    "name": v.name,
                    }
            displayList.append(vd)
            #print(vd["args"])

        result = {
            "total": ds.get("total"),
            "list": displayList
        }
        return jsonify(result), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400

@app.route('/add_dataset', methods=['POST'])
def add_dataset():
    inData = request.get_json()
    name = inData.get("name")
    if name is None or len(name) == 0:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    try:
        dataset.create_dataset(name)
    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    return jsonify({
        "code":0,
        "msg":"ok"
        }), 200

if __name__ == '__main__':
    #mossllm = load_moss("/root/MOSS-main/moss-moon-003-sft-int4")
    app.run(host="0.0.0.0",port=18888)
