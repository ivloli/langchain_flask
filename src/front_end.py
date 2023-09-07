from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.chat_models import ChatOpenAI
from streamlit.elements.write import json
from llms.LangChainMOSSWrapper import LangChainMOSSWrapper
from models import DataSet,Prompt,DataItem
from views import dataset, prompt, llm
from jitCl import jitChain
from typing import Dict
import streamlit as st
import pandas as pd
import os
import time

def list_csv_files_in_current_directory():
    current_directory = os.getcwd()
    csv_files = [file for file in os.listdir(current_directory) if file.endswith('.csv')]
    return csv_files

def file_exists(file_path):
    return os.path.exists(file_path)

def get_substrings_between_symbols(s, start_symbol='>', end_symbol='<'):
    substrings = []
    start_idx = 0

    while True:
        start_idx = s.find(start_symbol, start_idx)
        if start_idx == -1:
            break

        end_idx = s.find(end_symbol, start_idx + 1)
        if end_idx == -1:
            break

        substring = s[start_idx + 1: end_idx]
        substrings.append(substring)

        start_idx = end_idx + 1

    return substrings

def get_common_keys(list_of_dicts):
    if not list_of_dicts:
        return set()  # Return an empty set if the list is empty

    common_keys = set(list_of_dicts[0].keys())  # Initialize with the keys of the first dictionary

    for dictionary in list_of_dicts[1:]:
        common_keys.intersection_update(dictionary.keys())

    return list(common_keys)

def all_elements_in_list_a(a, b):
    # convert list to set
    set_a = set(a)
    set_b = set(b)

    return set_b.issubset(set_a)

st.set_page_config(
     page_title="MiniBot",
     page_icon=":robot_face:",
     layout="wide",
     initial_sidebar_state="expanded",
 )
#######################
#side bar
side = st.sidebar
if side.button("Refresh ♻️"):
    with st.spinner("Refreshing..."):
        time.sleep(1)
ps = prompt.get_prompts(1,50)
side.write("# Configration")
side.write("## Select Prompt")
side.info("total prompt:"+str(ps.get("total")))
psList = list[Prompt](ps.get("list"))
psMap: Dict[int, dict] = {}
#psDisplayList = []
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
    psMap[v.id] = vd
    side.table([vd])
    #psDisplayList.append(vd)

#side.table(psDisplayList)
selectedPrompt = side.radio(
        "Select Prompt",
        ["None"] + list(psMap.keys()),
        )
myPromptModel = None
if isinstance(selectedPrompt,int):
    myPromptModel = psMap.get(selectedPrompt)
    side.table([myPromptModel])

side.write("## Create Prompt")
with side.form("Create Prompt"):
    st.write("Create Prompt")
    initDict = {
            "name": "name of the prompt",
            "is_few_shot": True,
            "examples": [{
                "field1": "value1",
                "field2": "value2",
                }],
            "prefix": "prefix of the template",
            "suffix": "Answer is {answer}",
            "seperator": "\n",
            "template": "field1 is: {field1}, field2 is: {field2}"
            }
    jsonText = st.text_area("JSON Editor", json.dumps(initDict, indent=2))
    if st.form_submit_button("Save Prompt"):
        try:
            # 解析 JSON 字符串
            editedData = json.loads(jsonText)
            st.success("Successfully updated JSON data:")
            st.json(editedData)
            if editedData.get("seperator") is not None and editedData.get("seperator") == "":
                editedData["seperator"] = "\n"
            newUid = prompt.create_prompt(name=editedData.get("name"),examples=editedData.get("examples"),few_shot=editedData.get("is_few_shot"),prefix=editedData.get("prefix"),
                                suffix=editedData.get("suffix"),template=editedData.get("template"),seperator=editedData.get("seperator"))
            st.info("Create new Prompt: "+editedData.get("name")+" "+str(newUid))
        except json.JSONDecodeError:
            st.error("Invalid JSON format. Please enter valid JSON data.")

side.write("## Create DataSet")
with side.form("Create DataSet"):
    st.write("Create DataSet/DataItem")
    newDSname = st.text_input("input new dataset name","")
    if st.form_submit_button("Save DataSet"):
        newDSUid = dataset.create_dataset(name=newDSname)
        st.info("Create new DataSet: "+newDSname+" "+newDSUid)

side.write("## Create DataItem")
with side.form("Create DataItem"):
    uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt"])

    submit = st.form_submit_button("Upload")
    if uploaded_file is not None and submit: 
        # 获取上传的文件名
        filename = uploaded_file.name

        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 拼接保存文件的路径
        save_path = os.path.join(script_dir, filename)

        # 保存文件
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())

        # 显示成功上传的消息
        st.success(f"File '{filename}' has been uploaded and saved successfully.")

    csv_files = list_csv_files_in_current_directory()

    if not csv_files:
        st.warning("No CSV files found in the current directory.")

    selected_file = st.selectbox("Select a CSV file:", csv_files)

    selected_dataset = st.text_input("input name of dataset want to save in:", "")
    if st.form_submit_button("Save DataItem"):
        if selected_dataset == "":
            st.info("empty dataset name")
        elif not file_exists(selected_file):
            st.info("file not exists")
        else:
            st.write(f"Selected CSV file: {selected_file}")
            dataset.load_dataitems_csv_excel(dsname=selected_dataset,fname=selected_file)

###########################

@st.cache_resource
def load_moss(path: str):
    return LangChainMOSSWrapper(path)

@st.cache_resource
def load_chatGLM(url: str):
    return ChatOpenAI(openai_api_key="EMPTY", openai_api_base=url, model_name="chatglm2-6b")

@st.cache_resource
def load_defaultTemplate(systemContent: str):
    template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                   systemContent 
                )
            ),
            HumanMessagePromptTemplate.from_template("{text}"),
        ]
    )
    return template
###########################
#main page
st.write("# Main Page")
#mossllm = load_moss("/root/MOSS-main/moss-moon-003-sft-int4")
defaultTemplate = load_defaultTemplate("你是吉大正元大模型助手")
chatGLMllm = load_chatGLM("http://localhost:8888/v1")
dsList = dataset.get_datasets(1,50)

st.write("## DataSets")
datas = list[DataSet](dsList.get("list"))
dsMap = {}
for ds in datas:
    dsMap[ds.name] = ds.uid

selectedDs = st.radio(
    "Select DataSet",
    ["None"]+list(dsMap.keys()),
)
#dataset.load_dataitems_csv_excel(datas[0].uid, "output.csv")
if selectedDs != "None":
    items = dataset.get_dataitems(dsMap.get(selectedDs),1,50)
    st.write("## DataItems")
    st.info("total DataItems: " + str(items.get("total")))
    selectedDi = []
    
    if items.get("total") > 0:
        itemList = []
        itemDict: Dict[int, DataItem] = {}
        for v in list[DataItem](items.get("list")):
            vd = {
                    "id": v.id,
                    "args": v.args,
                    "uid": v.uid,
                    "dataset": v.dataset_uid,
                    }
            itemList.append(vd)
            itemDict[v.id] = v

        df = pd.DataFrame(itemList)
        st.dataframe(df)
        selectedDi = st.multiselect(
            "Select your DataItem from ID",
            itemDict.keys(),
        )

        itemListSelected = []
        itemUidSelected = []
        for id in selectedDi:
            item = itemDict.get(id)
            if item is not None:
                jsonDict = json.loads(str(item.args))
                itemListSelected.append(jsonDict)
                itemUidSelected.append(item.uid)

        st.write("### Selected DataItems")
        df = pd.DataFrame(itemListSelected)
        st.dataframe(df)
        commonKeys =  get_common_keys(itemListSelected)

if myPromptModel is not None:
    if myPromptModel.get("is_few_shot"):
        myTemplate = jitChain.generate_few_prompt_template(myPromptModel.get("examples"), myPromptModel.get("template"), myPromptModel.get("suffix"), 
                                                           myPromptModel.get("prefix"), myPromptModel.get("seperator"))
    else:
        myTemplate = jitChain.generate_prompt_template(myPromptModel.get("template"))
else:
    myTemplate = jitChain.generate_none_prompt_template()
templateInputKeys = myTemplate.input_variables
answerCol = None
if selectedDs == "None":
    if selectedPrompt == "None":
        question = st.text_area("input question","")
        inputList = [
                {"question": question}
                ]
        inputCommoneKeys = ["question"]
    else:
        st.warning("A Prompt should be used with in a DataSet")
        st.stop()
elif len(selectedDi) == 0:
    inputList = {}
    answerCol = st.text_input("input the Column to save the result","")
    for key in list(myTemplate.input_variables):
        value = st.text_area(f"Enter {key}:", "")
        inputList[key] = value
    inputUidList = [""]
    inputCommoneKeys = list(inputList.keys())
    inputList = [inputList]
        
else:
    answerCol = st.text_input("input the Column to save the result","")
    inputList = itemListSelected
    inputCommoneKeys = commonKeys
    inputUidList = itemUidSelected

if selectedDs == "None" and selectedPrompt != "None":
    st.warning("A Prompt should be used with in a DataSet")
    st.stop()
if not all_elements_in_list_a(inputCommoneKeys, templateInputKeys):
    st.warning("missing input key/keys")
    st.stop()



st.write("## LLMs")
stLLM = st.radio("Select LLM", ["ChatGLM2","OpenAI"])

with st.form("template"):
    if st.form_submit_button("Run"):
        if stLLM == "MOSS" or stLLM == "ChatGLM2":
            for idx,line in enumerate(inputList):
                inputText = myTemplate.format(**line)
                with st.spinner('Wait for it...'):
                    if stLLM == "MOSS":
                        outputText = mossllm(inputText)
                    else:
                        outputText = chatGLMllm(defaultTemplate.format_messages(text=inputText))
                result = get_substrings_between_symbols(outputText.content+"<")
                longest_substring = max(result, key=len)
                #st.info(result)
                st.info(longest_substring)
                if answerCol is not None and len(answerCol) > 0 :
                    line[answerCol] = longest_substring
                    uid = inputUidList[idx]
                    if len(uid) > 0:
                        dataset.update_dataitem(uid=uid, args=line)
                    else:
                        dataset.add_dataitem(ds_uid=dsMap.get(selectedDs), args=line)
                        

        elif stLLM == "OpenAI":
            myChain = LLMChain(llm=OpenAI(temperature=0, openai_api_key=st.secrets["openai_api_key"]),prompt=myTemplate)
            if myChain is not None: 
                for idx, line in enumerate(inputList):
                    with st.spinner('Wait for it...'):
                        result = myChain.run(**line)
                        time.sleep(1)
                    st.info(result)
                    if answerCol is not None and len(answerCol) > 0 :
                        line[answerCol] = result
                        uid = inputUidList[idx]
                        if len(uid) > 0:
                            dataset.update_dataitem(uid=uid, args=line)
                        else:
                            dataset.add_dataitem(ds_uid=dsMap.get(selectedDs), args=line)

            else:
                st.info("Not ready")

###########################
