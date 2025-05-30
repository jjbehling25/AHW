import os, json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ──────────────────────────────────────────────────────────────
# Load API key
# ──────────────────────────────────────────────────────────────
if os.path.exists(".env"):
    load_dotenv()  # for local dev
client = OpenAI(api_key=st.getenv("OPENAI_API_KEY"))

# ──────────────────────────────────────────────────────────────
# Helper to send messages
# ──────────────────────────────────────────────────────────────
def chat_with_agent(system_prompt, history):
    msgs = [{"role":"system","content":system_prompt}]
    for m in history:
        msgs.append({"role":"user","content":m})
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=msgs
    )
    return res.choices[0].message.content.strip()

# ──────────────────────────────────────────────────────────────
# Load system prompts
# ──────────────────────────────────────────────────────────────
with open("prompts/agent_a.txt", encoding="utf-8") as f:
    agent_a_sys = f.read()
with open("prompts/agent_b.txt", encoding="utf-8") as f:
    agent_b_sys = f.read()

# ──────────────────────────────────────────────────────────────
# Session state for conversation
# ──────────────────────────────────────────────────────────────
st.title("🔄 Multi-Agent Workflow")

if "a_history" not in st.session_state:
    st.session_state.a_history = []
if "a_reply" not in st.session_state:
    # kick off Agent A
    st.session_state.a_reply = chat_with_agent(agent_a_sys, [])
if "outline" not in st.session_state:
    st.session_state.outline = None

# ──────────────────────────────────────────────────────────────
# Agent A loop until status: complete
# ──────────────────────────────────────────────────────────────
if st.session_state.outline is None:
    st.subheader("Agent A is gathering info")
    st.markdown(f"> {st.session_state.a_reply}")
    user_input = st.text_input("Your answer:", key="input_a")
    if st.button("Submit Answer"):
        st.session_state.a_history.append(st.session_state.input_a)
        reply = chat_with_agent(agent_a_sys, st.session_state.a_history)
        st.session_state.a_reply = reply
        st.session_state.input_a = ""
        # check for completion
        if "status: complete" in reply.lower():
            payload = reply.split("status: complete",1)[1].strip()
            st.session_state.outline = json.loads(payload)
            st.experimental_rerun()

# ──────────────────────────────────────────────────────────────
# Once outline is ready → show it and run Agent B
# ──────────────────────────────────────────────────────────────
else:
    st.success("✅ Agent A finished!")
    st.json(st.session_state.outline)

    if "b_reply" not in st.session_state:
        if st.button("Generate Final Output"):
            out = chat_with_agent(agent_b_sys, [json.dumps(st.session_state.outline)])
            st.session_state.b_reply = out

    if "b_reply" in st.session_state:
        st.subheader("Agent B’s Response")
        st.write(st.session_state.b_reply)
