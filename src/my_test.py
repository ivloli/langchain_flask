from langchain.llms import OpenAI
from streamlit.elements.write import json
from models import DataSet,Prompt,DataItem
from views import dataset, prompt, llm
from jitCl import jitChain
from typing import Dict
import streamlit as st
import pandas as pd
import os

def file_exists(file_path):
    return os.path.exists(file_path)

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

#######################
#side bar
side = st.sidebar
ps = prompt.get_prompts(1,50)
side.write("Select Prompt")
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

with side.form("Create DataSet/DataItem"):
    st.write("Create DataSet/DataItem")
    newDSname = st.text_input("input new dataset name","")
    if st.form_submit_button("Save DataSet"):
        newDSUid = dataset.create_dataset(name=newDSname)
        st.info("Create new DataSet: "+newDSname+" "+newDSUid)

    dsname = st.text_input("input name of dataset want to save in:", "")
    diName = st.text_input("input csv file path:", "")
    if st.form_submit_button("Save DataItem"):
        if dsname == "":
            st.info("empty uid")
        elif not file_exists(diName):
            st.info("file not exists")
        else:
            dataset.load_dataitems_csv_excel(dsname==dsname,fname=diName)

with st.container():
    llmPath = side.text_input("input path of llm:", "")
###########################

###########################
#main page
dsList = dataset.get_datasets(1,50)

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

    st.info("total: " + str(items.get("total")))

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
    for id in selectedDi:
        item = itemDict.get(id)
        if item is not None:
            jsonDict = json.loads(str(item.args))
            itemListSelected.append(jsonDict)

    st.info("selected DataItems")
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

if selectedDs == "None":
    if selectedPrompt == "None":
        question = st.text_area("input question","")
        inputList = [
                {"question": question}
                ]
        inputCommoneKeys = ["question"]
    else:
        inputList = {}
        for key in list(myTemplate.input_variables):
            value = st.text_input(f"Enter {key}:", "")
            inputList[key] = value
        inputCommoneKeys = get_common_keys([inputList])
        
else:
    inputList = itemListSelected
    inputCommoneKeys = commonKeys
if not all_elements_in_list_a(inputCommoneKeys, templateInputKeys):
    st.info("missing input key/keys")
    st.stop()



stLLM = st.radio("Select LLM", ["MOSS","OpenAI"])
if st.button("Start"):
    if stLLM == "OpenAI":
        myLLM = OpenAI(temperature=0, openai_api_key=st.secrets["openai_api_key"])
    elif stLLM == "MOSS":
        myLLM = llm.get_llm(name="moss")
    myChain = jitChain.generate_chain(inputllm=myLLM,template=myTemplate)

    if myChain is not None: 
        if not isinstance(inputList,list):
            inputList = [inputList]
        result = myChain.apply(inputList)
        st.info(result)
        vs = []
        for data in result:
            v = data.get("text")
            if v is not None and v != "":
                vs.append(v)
        df = pd.DataFrame(vs)
        if len(vs) == 1:
            st.info(vs[0])
        else:
            st.dataframe(df)

    else:
        st.info("Not ready")

###########################
