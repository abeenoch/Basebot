import streamlit as st
from app import chat_graph, DevChatState

# Initialize Streamlit
st.title("DevBot for Base Network Development")

# Maintain session state for the conversation
if "state" not in st.session_state:
    st.session_state.state = {"messages": [], "preferences": {}, "finished": False}

# Render the conversation messages
for msg in st.session_state.state["messages"]:
    role = "user" if msg.get("type") == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(msg['content'])

# Input box for user input
if prompt := st.chat_input("Your message:"):
    # Add user's message to the state
    st.session_state.state["messages"].append({"type": "user", "content": prompt})

    # Invoke the chat graph with the current state and get the updated state
    st.session_state.state = chat_graph.invoke(st.session_state.state)

    # After invoking, ensure the chatbot response is part of the session state and displayed
    # Assuming chat_graph.invoke modifies the state and includes the response
    chatbot_response = st.session_state.state["messages"][-1]["content"]  # The last message is the response
    if chatbot_response:
        # Display the chatbot response in the interface
        with st.chat_message("assistant"):
            st.markdown(chatbot_response)
