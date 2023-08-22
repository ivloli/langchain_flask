from flask import Flask, request, jsonify, Response, stream_with_context, Blueprint
import helper
import time, json, simplejson
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
#from llms.LangChainMOSSWrapper import LangChainMOSSWrapper
from models import DataSet,Prompt,DataItem
from views import dataset, prompt
from jitCl import jitChain
from typing import Dict
import pandas as pd
import os

template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=(
                "你是吉大正元大模型机器人，可以帮助人们回答问题"
            )
        ),
        HumanMessagePromptTemplate.from_template("{text}"),
    ]
)
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 定义一个接收 GET 请求的视图函数
@app.route('/api/hello', methods=['GET'])
def hello():
    name = request.args.get('name', 'Guest')
    return f'Hello, {name}!'

# 定义一个接收 POST 请求的视图函数
@app.route('/api/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify(data)

def generate_numbers():
    for i in range(1, 11):
        yield str(i)
        time.sleep(1)

@app.route('/api/count', methods=['GET'])
def count():
    return Response(stream_with_context(generate_numbers()), content_type='text/plain')

@app.route('/api/list_prompt', methods=['GET'])
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
                    "uid": v.uid,
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

@app.route('/api/delete_prompt', methods=['DELETE'])
def delete_prompt():
    uid = request.args.get('uid','')
    if len(uid) == 0:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400
    try:
        prompt.delete_prompt(uid)
    except ValueError as e:
        return jsonify({"code":-1,"msg": "Invalid input."+str(e)}), 400
    return jsonify({
        "code":0,
        "msg":"ok"
        }), 200

@app.route('/api/add_edit_prompt', methods=['POST'])
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

@app.route('/api/get_prompt_columns', methods=['get'])
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

@app.route('/api/list_dataitem', methods=['GET'])
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
        return simplejson.dumps(result, ignore_nan=True), 200, {'Content-Type': 'application/json; charset=utf-8'}

    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400

@app.route('/api/delete_dataitem', methods=['DELETE'])
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

@app.route('/api/get_csv_list_dataitem', methods=['GET'])
def get_csv_list_dataitem():
    fileList = helper.list_csv_files_in_sub_directory(app.config['UPLOAD_FOLDER'])
    return jsonify({
        "list": fileList or []
        }),200

def get_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload_csv_dataitem', methods=['POST'])
def upload_csv_dataitem():
    if 'file' not in request.files:
        return jsonify({
            "code": -1,
            "msg": "No file part"
            }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return  jsonify({
            "code":-1,
            "msg":'No selected file'
            }), 400
    
    if file and allowed_file(file.filename):
        filename = get_unique_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({
            "code":0,
            "msg": f"File uploaded successfully, saved as {filename}"
            }), 200
    else:
        return jsonify({
            "code":-1,
            "msg":'Invalid file type'
            }), 400

@app.route('/api/import_dataitem_from_csv', methods=['GET'])
def import_dataitem_from_csv():
    filename = request.args.get('file_name','')
    dataset_name = request.args.get('dataset_name','')
    if filename == '':
        return  jsonify({
            "code":-1,
            "msg":'No selected file'
            }), 400
    if dataset_name == '':
        return  jsonify({
            "code":-1,
            "msg":'No selected dataset'
            }), 400
    if allowed_file(filename) == False:
        return  jsonify({
            "code":-1,
            "msg":'Invalid file type'
            }), 400
    try:
        dataset.load_dataitems_csv_excel(dsname=dataset_name, fname=os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except ValueError:
        return jsonify({"code":-1,"msg": "Import data item csv failed."}), 500
    return jsonify({
        "code":0,
        "msg": "ok"
        }), 200
    

@app.route('/api/list_dataset', methods=['GET'])
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

@app.route('/api/add_dataset', methods=['POST'])
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

@app.route('/api/list_llm', methods=['GET'])
def list_llm():
    return jsonify({
        "list": ["MOSS","OpenAI","ChatGLM2"]
        })

@app.route('/api/free_qa', methods=['POST'])
def free_qa():
    inputJson = request.get_json()
    try:
        if inputJson.get("llm") == "OpenAI":
            question = str(inputJson.get("question"))
            #result = openAILLM(question)
            result = "this is demo"
            return jsonify({
                "code":0,
                "msg":"ok",
                "result":result
                }), 200
        elif inputJson.get("llm") == "ChatGLM2":
            question = str(inputJson.get("question"))
            result = glm2llm(template.format_messages(text=question))
            return jsonify({
                "code":0,
                "msg":"ok",
                "result":result.content
                }), 200
        else:
            return jsonify({"code":-1,"msg": "Invalid llm"}), 400
    except ValueError:
        return jsonify({"code":-1,"msg": "Invalid input."}), 400

@app.route('/api/ask_llm', methods=['POST'])
def ask_llm():
    args = request.get_json()
    prt = args.get("prompt")
    prt_uid = prt.get("uid")
    myPromptModel = prompt.get_single_prompt(prt_uid)
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
    ditems = list(args.get("dataitems"))
    inputUidList = [] 
    inputList = []
    ds_uid = ""
    for item in ditems:
        uid = item.get("uid") or ""
        inputUidList.append(uid)
        item_args = item.get("args") or item
        inputList.append(item_args)
        ds_uid = item.get("dataset_uid") or ""
    myChain = LLMChain(llm=openAILLM,prompt=myTemplate)
    answerCol = args.get("column_save_to")
    res = []
    if myChain is not None: 
        for idx, line in enumerate(inputList):
            #result = myChain.run(**line)
            result = "this is demo"
            res.append(result)
            time.sleep(1)
            if answerCol is not None and len(answerCol) > 0 :
                line[answerCol] = result
                uid = inputUidList[idx]
                if len(uid) > 0:
                    dataset.update_dataitem(uid=uid, args=line)
                elif len(ds_uid) > 0:
                    dataset.add_dataitem(ds_uid=ds_uid, args=line)
    return jsonify({
        "code":0,
        "msg":"ok",
        "results": res
        }), 200





openAILLM=OpenAI(temperature=0.2, openai_api_key=os.environ.get("OPENAI_API_KEY"))
mossLLM = None
if __name__ == '__main__':
    #mossllm = load_moss("/root/MOSS-main/moss-moon-003-sft-int4")
    glm2llm = ChatOpenAI(openai_api_key="EMPTY", openai_api_base="http://localhost:8888/v1", model_name="chatglm2-6b")
    app.run(host="0.0.0.0",port=8501)

