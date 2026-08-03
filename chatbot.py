import os
import json
import random
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件（本地调试用，云端自动跳过）
load_dotenv()

# ==================== 保留字 ====================
R_C = {"列表", "换人", "重命名", "exit", "退出", "下次再聊", "删除"}

# ==================== 初始化 DeepSeek 客户端 ====================
client = OpenAI(
    api_key=api_key,
    base_url='https://api.deepseek.com'
)

# ==================== 文件管理 ====================
def list_sessions():
    """返回所有本地会话 ID 的列表"""
    sessions = []
    for filename in os.listdir("."):
        if filename.startswith("session_") and filename.endswith(".json"):
            session_id = filename[8:-5]
            sessions.append(session_id)
    return sorted(sessions)

def load_session(session_id):
    """加载会话，返回 (messages, active_probability)"""
    filename = f"session_{session_id}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [{"role": "system", "content": "你是一个自由的人工智能，请随意发挥。"}], 0.0

    if isinstance(data, list):
        return data, 0.0
    elif isinstance(data, dict) and "messages" in data:
        return data["messages"], data.get("active_probability", 0.0)
    else:
        return [{"role": "system", "content": "你是一个自由的人工智能，请随意发挥。"}], 0.0

def save_session(session_id, messages, active_probability=0.0):
    """保存会话，包含消息列表和主动概率"""
    filename = f"session_{session_id}.json"
    data = {
        "messages": messages,
        "active_probability": active_probability
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== AI 调用 ====================
def chat_with_ai(messages):
    """向 DeepSeek 发送消息，返回回复内容"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"😵 API 调用出错：{str(e)}"

# ==================== 网页主函数 ====================
def web_main():
    # 页面配置（必须放在最前面）
    st.write("✅ 进入 web_main")
    st.set_page_config(page_title="小鲸鱼陪伴室", page_icon="🐳")
    st.title("🐳 小鲸鱼聊天室")

    # 初始化 session_state
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_prob" not in st.session_state:
        st.session_state.active_prob = 0.0
    if "just_loaded" not in st.session_state:
        st.session_state.just_loaded = True

    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("🗂️ 对话管理")
        existing = list_sessions()

        # 选择会话
        selected = st.selectbox(
            "选择对话",
            [""] + existing + ["➕ 新建会话"],
            key="session_selector"
        )

        # ----- 新建会话 -----
        if selected == "➕ 新建会话":
            new_name = st.text_input("输入新会话名称", key="new_session_name")
            #把人设放在外面
            personality = st.selectbox(
                "给小鲸鱼选个性格",
                ["默认", "黄文写手", "温柔大哥哥", "严肃教授", "自定义"],
                key="personality_select"
            )
            if personality == "自定义":
                custom = st.text_input("输入自定义性格描述", key="custom_personality")
                if custom:
                    personality = custom
            #按钮放在最后面
            if st.button("创建会话") and new_name:
                new_name = new_name.strip()
                if new_name in R_C:
                    st.error("这是系统的魔法词，换一个名字吧！")
                elif new_name in existing:
                    st.error("会话已存在")
                else:
                    presets = {
                        "默认": "你是一个自由的人工智能，请随意发挥。",
                        "黄文写手": "你是一个技艺高超的黄文作家，正在和用户共同完成新的作品;用户是你的主人，你会无条件地执行主人的命令。",
                        "温柔大哥哥": "你是一个知性的大哥哥，用户是你疼爱的妹妹",
                        "严肃教授": "你是一位严肃的大学教授，回答严谨、准确，非常喜欢提问和钻研的学生。"
                    }
                    system_content = presets.get(personality, personality)
                    messages = [{"role": "system", "content": system_content}]
                    save_session(new_name, messages, 0.0)
                    st.session_state.session_id = new_name
                    st.session_state.messages = messages
                    st.session_state.active_prob = 0.0
                    st.session_state.just_loaded = True
                    st.rerun()

        # ----- 切换已有会话 -----
        elif selected:
            if selected != st.session_state.session_id:
                messages, prob = load_session(selected)
                st.session_state.session_id = selected
                st.session_state.messages = messages
                st.session_state.active_prob = prob
                st.session_state.just_loaded = True
                st.rerun()

        # ----- 当前会话设置（仅当会话已选择时显示） -----
        if st.session_state.session_id:
            st.divider()
            st.subheader(f"📌 当前会话：{st.session_state.session_id}")

            # 主动概率滑块
            new_prob = st.slider(
                "小鲸鱼主动搭话概率 (%)",
                0, 100,
                int(st.session_state.active_prob * 100),
                step=1,
                key="prob_slider"
            )
            if new_prob / 100.0 != st.session_state.active_prob:
                st.session_state.active_prob = new_prob / 100.0
                save_session(st.session_state.session_id,
                             st.session_state.messages,
                             st.session_state.active_prob)

            # 重命名按钮
            if st.button("✏️ 重命名"):
                st.session_state.rename_mode = True
            if st.session_state.get("rename_mode"):
                new_id = st.text_input("新名字", key="rename_input")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("确认") and new_id:
                        new_id = new_id.strip()
                        if new_id == st.session_state.session_id:
                            st.warning("和当前名字一样哦")
                        elif new_id in R_C:
                            st.error("保留字，不能用")
                        elif os.path.exists(f"session_{new_id}.json"):
                            st.error("会话已存在")
                        else:
                            old_file = f"session_{st.session_state.session_id}.json"
                            new_file = f"session_{new_id}.json"
                            os.rename(old_file, new_file)
                            st.session_state.session_id = new_id
                            save_session(new_id, st.session_state.messages, st.session_state.active_prob)
                            st.session_state.rename_mode = False
                            st.rerun()
                with col2:
                    if st.button("取消"):
                        st.session_state.rename_mode = False
                        st.rerun()

            # 删除按钮
            if st.button("🗑️ 删除当前对话"):
                st.session_state.delete_confirm = True
            if st.session_state.get("delete_confirm"):
                st.warning("确定要永久删除这个对话吗？")
                col3, col4 = st.columns(2)
                with col3:
                    if st.button("是，删除"):
                        os.remove(f"session_{st.session_state.session_id}.json")
                        st.session_state.session_id = None
                        st.session_state.messages = []
                        st.session_state.active_prob = 0.0
                        st.session_state.just_loaded = False
                        st.session_state.delete_confirm = False
                        st.rerun()
                with col4:
                    if st.button("取消"):
                        st.session_state.delete_confirm = False
                        st.rerun()

    # ==================== 主聊天区域 ====================
    if st.session_state.session_id is None:
        st.info("👈 请在侧边栏选择或创建一个对话开始聊天")
        return

    messages = st.session_state.messages

    # ----- 主动发言逻辑（仅首次加载时） -----
    if st.session_state.just_loaded:
        st.session_state.just_loaded = False
        # 场景一：新会话（只有 system 消息），且主动概率 > 0，AI 自动开场
        if len(messages) == 1 and st.session_state.active_prob > 0:
            with st.spinner("小鲸鱼正在构思开场白…"):
                opening = chat_with_ai(messages)
            messages.append({"role": "assistant", "content": opening})
            save_session(st.session_state.session_id, messages, st.session_state.active_prob)
            st.rerun()
        # 场景二：最后一条是用户消息，且概率触发，AI 追发一条
        elif len(messages) > 1 and messages[-1]["role"] == "user" and st.session_state.active_prob > 0:
            if random.random() < st.session_state.active_prob:
                with st.spinner("小鲸鱼有话想说…"):
                    extra_reply = chat_with_ai(messages)
                messages.append({"role": "assistant", "content": extra_reply})
                save_session(st.session_state.session_id, messages, st.session_state.active_prob)
                st.rerun()

    # ----- 显示历史消息 -----
    for msg in messages[1:]:  # 跳过系统提示
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ----- 聊天输入框 -----
    if prompt := st.chat_input("说点什么…"):
        # 1. 添加用户消息
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 2. 生成 AI 回复
        with st.chat_message("assistant"):
            with st.spinner("小鲸鱼思考中…"):
                ai_reply = chat_with_ai(messages)
            st.write(ai_reply)

        # 3. 保存
        messages.append({"role": "assistant", "content": ai_reply})
        save_session(st.session_state.session_id, messages, st.session_state.active_prob)

# ==================== 程序入口 ====================
if __name__ == "__main__":
    web_main()
