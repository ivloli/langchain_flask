from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
import streamlit as st
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate

template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=(
                "You are a helpful assistant"
            )
        ),
        HumanMessagePromptTemplate.from_template("{text}"),
    ]
)


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

if "messages" not in st.session_state:
    st.session_state["messages"] = [ChatMessage(role="assistant", content="How can I help you?")]

for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if prompt := st.chat_input():
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())
        #llm = ChatOpenAI(openai_api_key="EMPTY", streaming=True, callbacks=[stream_handler], verbose=True, openai_api_base="http://localhost:8888/v1", model_name="chatglm2-6b")
        llm = ChatOpenAI(openai_api_key="EMPTY", openai_api_base="http://localhost:8888/v1", model_name="chatglm2-6b")
        #response = llm(st.session_state.messages)
        response = llm(template.format_messages(text=prompt))
        st.write(response.content)
