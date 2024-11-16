import streamlit as st
from app import chat_graph, DevChatState

# Initialize Streamlit
st.title("DevBot for Base Network Development")

# Maintain session state for the conversation
if "state" not in st.session_state:
    st.session_state.state = {"messages": [], "preferences": {}, "finished": False}

# Render the conversation messages
st.markdown("## Chat Conversation")
if st.session_state.state["messages"]:
    for msg in st.session_state.state["messages"]:
        role = "User" if msg.get("type") == "user" else "DevBot"
        st.markdown(f"**{role}:** {msg['content']}")

# Input box for user input
user_input = st.text_input("Your message:", key="user_input")
if user_input:
    # Add user's message to the state
    st.session_state.state["messages"].append({"type": "user", "content": user_input})

    # Invoke the chat graph with the current state and get the updated state
    st.session_state.state = chat_graph.invoke(st.session_state.state)

    # Display the chatbot response in the interface
    chatbot_response = st.session_state.state["messages"][-1]["content"]
    st.markdown(f"**DevBot:** {chatbot_response}")

    # Clear the input box after processing
    st.session_state.user_input = ""

# Button to end the session
if st.button("End Conversation"):
    st.session_state.state["finished"] = True
    st.write("Thank you for using DevBot!")
    st.stop()
