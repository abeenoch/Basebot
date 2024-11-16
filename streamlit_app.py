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
user_input = st.chat_input("Your message:")
if user_input:
    # Add user's message to the state
    st.session_state.state["messages"].append({"type": "user", "content": user_input})

    # Invoke the chat graph with the current state and update the state
    try:
        st.session_state.state = chat_graph.invoke(st.session_state.state)
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")

    # Ensure the chatbot response is part of the session state and displayed
    if st.session_state.state["messages"]:
        last_message = st.session_state.state["messages"][-1]
        if last_message.get("type") == "assistant":
            with st.chat_message("assistant"):
                st.markdown(last_message.get("content", ""))

# Button to end the session
if st.button("End Conversation"):
    st.session_state.state["finished"] = True
    st.write("Thank you for using DevBot!")
    st.stop()
