import streamlit as st

# 原始字典
my_dict = {
    "name": "",
    "age": "",
    "city": ""
}

# 遍历字典的每个键，并为每个键创建文本输入框
for key in my_dict.keys():
    value = st.text_input(f"Enter {key}:", my_dict[key])
    my_dict[key] = value

# 显示结果
st.write("Updated Dictionary:", my_dict)

