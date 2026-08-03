import streamlit as st#引入streamline库，并起别名‘st‘，方便调用
import os,json
from openai import OpenAI

#初始化客户端
api_key="sk-76d41328a22c4a11ba32686539b2cf2d"  # 临时用，不要上传到 GitHub
client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')


st.title("小鲸鱼聊天")
#会话记忆列表
if'messages' not in st.session_state:
    st.session_state.messages=[{"role":'system','content':'你是一个自由的人工智能。'}]

#显示历史消息
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

#用户输入
if prompt :=st.chat_input("你想说什么？"):
    st.session_state.messages.append({"role":'user','content':prompt})
    with st.chat_message('user'):
        st.write(prompt)

    with st.chat_message('assistant'):
        with st.spinner('小鲸鱼思考中'):
            response=client.chat.completions.create(
                model='deepseek-chat',
                messages=st.session_state.messages
            )
            reply=response.choices[0].messages.content
        st.write(reply)
    st.session_state.messages.append({"role":'assistant','content':reply})