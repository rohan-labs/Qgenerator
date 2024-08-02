"""
app.py
"""
import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock 

st.title("💬 Qgenerator")
st.write(
    "This is a chatbot used to generate responses. "
    "To use this app, you need to provide an OpenAI API key."
    "You can also learn how to build questions step by step by [following our tutorial](https://longhaired-quail-da4.notion.site/Question-generation-guide-f023286e149b43b6a0d1e0562305deb4)."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

ASSISTANT_ID = "asst_q9HBwNTS9qcHq4eHUTmJH0jH"

# Initialise the OpenAI client, and retrieve the assistant
client = OpenAI(api_key=openai_api_key)
assistant = client.beta.assistants.retrieve(assistant_id="asst_q9HBwNTS9qcHq4eHUTmJH0jH")

# Initialise session state to store conversation history locally to display on UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Title
st.title("Assistants API Streaming")

# Display messages in chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Textbox and streaming process
if user_query := st.chat_input("Ask me a question"):

    # Create a new thread if it does not exist
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # Display the user's query
    with st.chat_message("user"):
        st.markdown(user_query)

    # Store the user's query into the history
    st.session_state.chat_history.append({"role": "user",
                                          "content": user_query})
    
    # Add user query to the thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_query
        )

    # Stream the assistant's reply
    with st.chat_message("assistant"):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            stream=True
            )
        
        # Empty container to display the assistant's reply
        assistant_reply_box = st.empty()
        
        # A blank string to store the assistant's reply
        assistant_reply = ""

        # Iterate through the stream 
        for event in stream:
            # There are various types of streaming events
            # See here: https://platform.openai.com/docs/api-reference/assistants-streaming/events

            # Here, we only consider if there's a delta text
            if isinstance(event, ThreadMessageDelta):
                if isinstance(event.data.delta.content[0], TextDeltaBlock):
                    # empty the container
                    assistant_reply_box.empty()
                    # add the new text
                    assistant_reply += event.data.delta.content[0].text.value
                    # display the new text
                    assistant_reply_box.markdown(assistant_reply)
        
        # Once the stream is over, update chat history
        st.session_state.chat_history.append({"role": "assistant",
                                              "content": assistant_reply})
