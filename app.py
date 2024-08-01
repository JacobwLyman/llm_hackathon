import streamlit as st
import json
from dotenv import load_dotenv
import os
import time
import openai
import comet_llm

load_dotenv('.env')
comet_llm.init(api_key=os.getenv('COMET_API_KEY'), project='llm-hackathon')

# Set up environment variables for OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load system prompt
system_prompt = "You are an experienced assistant for the Comet platform, which is designed to enhance the ML lifecycle through efficient experiment tracking, model management, and production monitoring. You will: 1. Assist users with integrating Comet SDKs and APIs into their projects. 2. Help users write and troubleshoot Python code for creating custom panels. 3. Answer any questions about the Comet platform and its use cases. 4. Offer advice on best practices for using Comet to streamline ML workflows. Ensure your responses are thorough, accurate, and easy to understand."

selected_model = "gpt-3.5-turbo"

# Load knowledge base for keyword search
def load_knowledge_base(directory):
    knowledge_base = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as file:
                knowledge_base[filename] = json.load(file)
    return knowledge_base

knowledge_base = load_knowledge_base("./knowledge_base/rag_db")

def find_relevant_content(user_prompt, knowledge_base):
    # Simple keyword matching to find relevant documents
    relevant_content = []
    for key, doc in knowledge_base.items():
        if any(keyword.lower() in doc['content'].lower() for keyword in user_prompt.split()):
            relevant_content.append(doc['content'])
    return "\n".join(relevant_content)

def get_chatgpt_response(user_prompt):
    start_time = time.time()

    # Query knowledge base for relevant content
    related_content = find_relevant_content(user_prompt, knowledge_base)

    # Define the message history with system and user messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": related_content}  # Include related content in the conversation
    ]

    # Include previous conversation history
    for message in st.session_state.conversation:
        messages.append({"role": "user", "content": message['question']})
        messages.append({"role": "assistant", "content": message['answer']})

    # Add current user prompt
    messages.append({"role": "user", "content": user_prompt})

    # Use the new API interface
    try:
        response = openai.ChatCompletion.create(
            model=selected_model,
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )
        
        response_text = response.choices[0].message['content'].strip()
    except openai.error.OpenAIError as e:
        response_text = f"An error occurred: {str(e)}"

    end_time = time.time()
    duration = end_time - start_time

    # Log the prompts and response using Comet LLM
    trace = comet_llm.log_prompt(
        prompt=user_prompt,
        metadata={'model': selected_model,
                  'system_prompt': system_prompt},
        output=response_text,
        duration=duration
    )

    return response_text, trace.id

# Initialize session state for conversation history
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

# Function to clear conversation
def clear_conversation():
    st.session_state.conversation = []

# Function to log user feedback
def log_feedback(trace_id, score):
    comet_llm.log_user_feedback(id=trace_id, score=score)

# Sidebar content
st.sidebar.title("About This App")
st.sidebar.markdown("""
### Comet Chatbot Assistant

**How to Use the App:**
1. Enter your question about the Comet platform, SDKs, or general Python help in the input box.
2. Press `Enter` to submit your question.
3. View the bot's response in the conversation history.
4. Provide feedback using the thumbs up (👍) or thumbs down (👎) buttons.

**What It Does:**
This chatbot is designed to assist you with:
- Integrating Comet SDKs and APIs into your existing codebases.
- Writing Python panel code.
- Answering questions related to the Comet platform.

**About Comet:**
Comet is a platform that allows data scientists and machine learning engineers to track, compare, explain, and optimize their experiments and models. Comet provides tools to manage and visualize your machine learning projects, helping you build better models faster.
""")

# Main UI
st.title("Comet Chatbot Assistant")
st.write("Ask a question about the Comet platform, SDKs, or general Python help:")

# Display conversation history
conversation_container = st.container()
with conversation_container:
    for i, message in enumerate(st.session_state.conversation):
        user_message_html = f"""
        <div style='display: inline-block; max-width: 80%; border: 1px solid #007bff; padding: 10px; border-radius: 10px; margin: 10px 0; background-color: #007bff; text-align: right; color: #ffffff;'>
            <strong>You:</strong> {message['question']}
        </div>
        """
        bot_message_html = f"""
        <div style='display: inline-block; max-width: 80%; border: 1px solid #ccc; padding: 10px; border-radius: 10px; margin: 10px 0; background-color: #e9e9e9; text-align: left; color: #000;'>
            <strong>Bot:</strong> {message['answer']}
        </div>
        """
        st.markdown(user_message_html, unsafe_allow_html=True)
        st.markdown(bot_message_html, unsafe_allow_html=True)
        col1, col2, _ = st.columns([1, 1, 8])
        with col1:
            if st.button('👍', key=f'upvote_{i}'):
                log_feedback(message['trace_id'], 1.0)
        with col2:
            if st.button('👎', key=f'downvote_{i}'):
                log_feedback(message['trace_id'], 0.0)
    st.write("\n")

# Input and buttons at the bottom
user_input = st.text_input("Your message:", key='input', on_change=lambda: st.session_state.submit_input())

# Automatically submit input when return key is pressed
if 'submit_input' not in st.session_state:
    def submit_input():
        if st.session_state.input:
            with st.spinner("Thinking..."):
                response, trace_id = get_chatgpt_response(st.session_state.input)
                st.session_state.conversation.append({
                    'question': st.session_state.input,
                    'answer': response,
                    'trace_id': trace_id
                })
            st.session_state.input = ""  # Clear input field after submission
    st.session_state.submit_input = submit_input

# Clear conversation button
clear_button = st.button('Clear Conversation', on_click=clear_conversation)

# Style adjustments to make emoji buttons bigger
st.markdown("""
    <style>
        .stTextInput>div>div>input {
            padding: 10px;
        }
        .stButton>button {
            padding: 10px;
            font-size: 24px; /* Increase font size */
        }
    </style>
    """, unsafe_allow_html=True)
