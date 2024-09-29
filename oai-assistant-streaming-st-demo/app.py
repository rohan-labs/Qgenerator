import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock

st.set_page_config(layout="wide")

# Function for Perplexity AI chatbot
def get_perplexity_response(client, messages):
    response = client.chat.completions.create(
        model="llama-3.1-sonar-huge-128k-online",
        messages=messages,
        stream=True
    )
    return response

def stream_perplexity_response(response, placeholder):
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            placeholder.markdown(full_response + "▌")
    placeholder.markdown(full_response)
    return full_response

# Function for OpenAI Assistant chatbot
def stream_openai_response(client, thread_id, assistant_id, assistant_reply_box):
    stream = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        stream=True
    )
    
    assistant_reply = ""
    for event in stream:
        if isinstance(event, ThreadMessageDelta):
            if isinstance(event.data.delta.content[0], TextDeltaBlock):
                assistant_reply_box.empty()
                assistant_reply += event.data.delta.content[0].text.value
                assistant_reply_box.markdown(assistant_reply)
    
    return assistant_reply

# Main application
def main():
    st.title("Dual Chatbot Application")

    chatbot_choice = st.selectbox("Choose a chatbot", ["Question generator", "Explanation generator"])

    if chatbot_choice == "Question generator":
        st.header("Question generator")
        
        if "openai_api_key" not in st.session_state:
            st.session_state.openai_api_key = ""
        
        openai_api_key = st.text_input("OpenAI API Key", type="password", key="openai_key", value=st.session_state.openai_api_key)
        st.session_state.openai_api_key = openai_api_key
        
        if "openai_chat_history" not in st.session_state:
            st.session_state.openai_chat_history = []

        # Clear chat history button
        if st.button("Clear Chat History", key="clear_openai"):
            st.session_state.openai_chat_history = []
            st.session_state.pop('thread_id', None)
            st.experimental_rerun()

        # Create a container for chat history
        openai_chat_container = st.container()

        # Input field below chat history
        user_query = st.chat_input("Ask a question to OpenAI Assistant...", key="openai_input")

        # Display chat history in the container
        with openai_chat_container:
            for message in st.session_state.openai_chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if openai_api_key and user_query:
            openai_client = OpenAI(api_key=openai_api_key)
            ASSISTANT_ID = "asst_07BRpo8153fuKR4KpqM8iscm"

            if "thread_id" not in st.session_state:
                thread = openai_client.beta.threads.create()
                st.session_state.thread_id = thread.id

            with openai_chat_container:
                with st.chat_message("user"):
                    st.markdown(user_query)

            st.session_state.openai_chat_history.append({"role": "user", "content": user_query})
            
            openai_client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_query
            )

            with openai_chat_container:
                with st.chat_message("assistant"):
                    assistant_reply = stream_openai_response(openai_client, st.session_state.thread_id, ASSISTANT_ID, st.empty())
            
            st.session_state.openai_chat_history.append({"role": "assistant", "content": assistant_reply})

    elif chatbot_choice == "Explanation generator":
        st.header("Explanation generator")
        
        if "perplexity_api_key" not in st.session_state:
            st.session_state.perplexity_api_key = ""
        
        perplexity_api_key = st.text_input("Preclinify API Key", type="password", key="perplexity_key", value=st.session_state.perplexity_api_key)
        st.session_state.perplexity_api_key = perplexity_api_key
        
        if "perplexity_messages" not in st.session_state:
            st.session_state.perplexity_messages = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]

        # Clear chat history button
        if st.button("Clear Chat History", key="clear_perplexity"):
            st.session_state.perplexity_messages = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]
            st.experimental_rerun()

        # Create a container for chat history
        perplexity_chat_container = st.container()

        # Input field below chat history
        user_input = st.chat_input("Type your message for Perplexity AI...", key="perplexity_input")

        # Display chat history in the container
        with perplexity_chat_container:
            for message in st.session_state.perplexity_messages[1:]:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        if perplexity_api_key and user_input:
            perplexity_client = OpenAI(api_key=perplexity_api_key, base_url="https://api.perplexity.ai")

            st.session_state.perplexity_messages.append({"role": "user", "content": user_input})
            with perplexity_chat_container:
                with st.chat_message("user"):
                    st.write(user_input)
            
            response_stream = get_perplexity_response(perplexity_client, st.session_state.perplexity_messages)
            
            with perplexity_chat_container:
                with st.chat_message("assistant"):
                    ai_response = stream_perplexity_response(response_stream, st.empty())
            
            st.session_state.perplexity_messages.append({"role": "assistant", "content": ai_response})

if __name__ == "__main__":
    main()
