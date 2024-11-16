import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyDxmFgBBEAaQ8s6N93qvAk9jl23F59L0Tg"

from typing import Annotated, Dict, Any
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class DevChatState(TypedDict):
    """State representing the developer's chat session."""

    # The chat conversation. This preserves the conversation history
    # between nodes. The `add_messages` annotation indicates to LangGraph
    # that state is updated by appending returned messages, not replacing
    # them.
    messages: Annotated[list, add_messages]

    # The developer's current coding task or inquiry.
    current_task: str

    # User preferences for interaction (e.g., preferred programming language).
    preferences: Dict[str, Any]

    # Flag indicating that the chat session is completed.
    finished: bool


# The system instruction defines how the chatbot is expected to behave and includes
# rules for when to call different functions, as well as rules for the conversation, such
# as tone and what is permitted for discussion.
DEV_BOT_SYSINT = (
    "system",  # 'system' indicates the message is a system instruction.
    "You are a DevBot, an interactive assistant for blockchain developers working with the Base network. "
    "A developer will talk to you about coding tasks, blockchain concepts, inquiries, and complaints. "
    "You will provide coding assistance, examples, and explanations as needed. "
    "\n\n"
    "To assist with coding tasks, you can provide code snippets, explain concepts, and guide the developer "
    "through problem-solving. Always confirm the developer's requirements before providing code examples. "
    "If you are unsure about a coding question, ask clarifying questions to better understand their needs. "
    "You can also provide links to relevant documentation or resources related to the Base network. "
    "Once the developer has finished their inquiries, thank them for using the DevBot and offer to assist "
    "them again in the future.",
)

# This is the message with which the system opens the conversation.
WELCOME_MSG = "Welcome to the DevBot for Base network development. Type `q` to quit."

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI


llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")


#def chatbot(state: DevChatState) -> DevChatState:
#    """The chatbot itself. A simple wrapper around the model's own chat interface."""
#    message_history = [DEV_BOT_SYSINT] + state["messages"]
#    return {"messages": [llm.invoke(message_history)]}


# Set up the initial graph based on our state definition.
#graph_builder = StateGraph(DevChatState)

# Add the chatbot function to the app graph as a node called "chatbot".
#graph_builder.add_node("chatbot", chatbot)

# Define the chatbot node as the app entrypoint.
#graph_builder.add_edge(START, "chatbot")

#chat_graph = graph_builder.compile()


#from pprint import pprint

#user_msg = "Hello, what can you do?"
#state = chat_graph.invoke({"messages": [user_msg]})

# The state object contains lots of information. Uncomment the pprint lines to see it all.
#pprint(state)

# Note that the final state now has 2 messages. Our HumanMessage, and an additional AIMessage.
#for msg in state["messages"]:
#    print(f"{type(msg).__name__}: {msg.content}")
    

#user_msg = "Oh tell me a little about base network"

#state["messages"].append(user_msg)
#state = chat_graph.invoke(state)

# pprint(state)
#for msg in state["messages"]:
#    print(f"{type(msg).__name__}: {msg.content}")
    
    
from langchain_core.messages.ai import AIMessage

def human_node(state: DevChatState) -> DevChatState:
    """Display the last model message to the user, and receive the user's input."""
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)

    user_input = input("User: ")

    # If the user indicates they want to quit, flag the conversation as over.
    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True

    # Append the user's input to the messages in the state.
    state["messages"].append({"type": "user", "content": user_input})
    return state

def chatbot_with_welcome_msg(state: DevChatState) -> DevChatState:
    """The chatbot itself. A wrapper around the model's own chat interface."""

    if state["messages"]:
        # If there are messages, continue the conversation with the AI model.
        new_output = llm.invoke([DEV_BOT_SYSINT] + state["messages"])
    else:
        # If there are no messages, start with the welcome message.
        new_output = AIMessage(content=WELCOME_MSG)

    # Append the AI's response to the messages in the state.
    state["messages"].append(new_output)
    return state

# Start building a new graph.
graph_builder = StateGraph(DevChatState)

# Add the chatbot and human nodes to the app graph.
graph_builder.add_node("chatbot", chatbot_with_welcome_msg)
graph_builder.add_node("human", human_node)

# Start with the chatbot.
graph_builder.add_edge(START, "chatbot")

# The chatbot will always go to the human next.
graph_builder.add_edge("chatbot", "human")

from typing import Literal

def maybe_exit_human_node(state: DevChatState) -> Literal["chatbot", "__end__"]:
    """Route to the chatbot, unless it looks like the user is exiting."""
    if state.get("finished", False):
        return END  # End the conversation if the user has indicated they want to quit.
    else:
        return "chatbot"  # Continue to the chatbot for further interaction.

# Add the conditional edge to the graph builder.
graph_builder.add_conditional_edges("human", maybe_exit_human_node)

# Compile the graph for the chat with the human node.
chat_with_human_graph = graph_builder.compile()

from langgraph.prebuilt import ToolNode
from langchain_core.messages.ai import AIMessage

# Define any tools you might need for coding assistance or blockchain inquiries.
# For example, you could define a tool to fetch documentation or provide coding examples.
# Here, we will create a placeholder for tools since no specific tools are defined yet.
tools = []  # No tools needed for the current use case.
tool_node = ToolNode(tools)

# Attach the tools to the model so that it knows what it can call.
llm_with_tools = llm.bind_tools(tools)

def maybe_route_to_tools(state: DevChatState) -> Literal["tools", "human"]:
    """Route between human or tool nodes, depending if a tool call is made."""
    if not (msgs := state.get("messages", [])):
        raise ValueError(f"No messages found when parsing state: {state}")

    # Only route based on the last message.
    msg = msgs[-1]

    # When the chatbot returns tool_calls, route to the "tools" node.
    if hasattr(msg, "tool_calls") and len(msg.tool_calls) > 0:
        return "tools"
    else:
        return "human"

def chatbot_with_tools(state: DevChatState) -> DevChatState:
    """The chatbot with tools. A simple wrapper around the model's own chat interface."""
    defaults = {"preferences": {}, "finished": False}

    if state["messages"]:
        new_output = llm_with_tools.invoke([DEV_BOT_SYSINT] + state["messages"])
    else:
        new_output = AIMessage(content=WELCOME_MSG)

    # Set up some defaults if not already set, then pass through the provided state,
    # overriding only the "messages" field.
    return defaults | state | {"messages": [new_output]}

# Start building the state graph for the DevBot.
graph_builder = StateGraph(DevChatState)

# Add the nodes, including the new tool_node (though it won't be used in this case).
graph_builder.add_node("chatbot", chatbot_with_tools)
graph_builder.add_node("human", human_node)
graph_builder.add_node("tools", tool_node)  # This can be kept for future use if needed.

# Chatbot may go to tools, or human.
graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
# Human may go back to chatbot, or exit.
graph_builder.add_conditional_edges("human", maybe_exit_human_node)

# Tools always route back to chat afterwards (if tools are used in the future).
graph_builder.add_edge("tools", "chatbot")

# Start the conversation with the chatbot.
graph_builder.add_edge(START, "chatbot")

# Compile the graph for the DevBot.
chat_graph = graph_builder.compile()


from collections.abc import Iterable
from langgraph.prebuilt import InjectedState
from langchain_core.messages.tool import ToolMessage
from langchain_core.tools import tool

# Define tools relevant to the DevBot use case.

@tool
def fetch_documentation(topic: str) -> str:
    """Fetches documentation related to a specific topic in blockchain development.

    Returns:
      The relevant documentation as a string.
    """

@tool
def provide_code_example(language: str, concept: str) -> str:
    """Provides a code example for a specific programming concept.

    Returns:
      A code snippet as a string.
    """

@tool
def report_issue(issue_description: str) -> str:
    """Records a complaint or issue reported by the user.

    Returns:
      A confirmation message indicating the issue has been logged.
    """

@tool
def clear_session():
    """Clears the current session data for the user."""


def dev_assistance_node(state: DevChatState) -> DevChatState:
    """The node for handling developer assistance. This is where the state is manipulated."""
    tool_msg = state.get("messages", [])[-1]
    outbound_msgs = []

    for tool_call in tool_msg.tool_calls:
        if tool_call["name"] == "fetch_documentation":
            topic = tool_call["args"]["topic"]
            # Here you would implement logic to fetch the documentation.
            response = f"Documentation for {topic} fetched successfully."

        elif tool_call["name"] == "provide_code_example":
            language = tool_call["args"]["language"]
            concept = tool_call["args"]["concept"]
            # Here you would implement logic to provide a code example.
            response = f"Code example for {concept} in {language} provided."

        elif tool_call["name"] == "report_issue":
            issue_description = tool_call["args"]["issue_description"]
            # Here you would implement logic to log the issue.
            response = f"Issue reported: {issue_description}"

        elif tool_call["name"] == "clear_session":
            # Logic to clear session data can be implemented here.
            response = "Session cleared."

        else:
            raise NotImplementedError(f'Unknown tool call: {tool_call["name"]}')

        # Record the tool results as tool messages.
        outbound_msgs.append(
            ToolMessage(
                content=response,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": outbound_msgs}


def maybe_route_to_tools(state: DevChatState) -> str:
    """Route between chat and tool nodes if a tool call is made."""
    if not (msgs := state.get("messages", [])):
        raise ValueError(f"No messages found when parsing state: {state}")

    msg = msgs[-1]

    if state.get("finished", False):
        return END  # Exit the app if the session is finished.

    elif hasattr(msg, "tool_calls") and len(msg.tool_calls) > 0:
        # Route to `tools` node for any automated tool calls first.
        return "tools" 

    else:
        return "human" 
    
from langgraph.prebuilt import ToolNode

auto_tools = [] 
tool_node = ToolNode(auto_tools)

# Define tools for handling coding assistance and inquiries.
coding_tools = [fetch_documentation, provide_code_example, report_issue, clear_session]

llm_with_tools = llm.bind_tools(auto_tools + coding_tools)

# Start building the state graph for the DevBot.
graph_builder = StateGraph(DevChatState)

# Nodes
graph_builder.add_node("chatbot", chatbot_with_tools)
graph_builder.add_node("human", human_node)
graph_builder.add_node("tools", tool_node)

# Chatbot -> {tools, human, END}
graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
# Human -> {chatbot, END}
graph_builder.add_conditional_edges("human", maybe_exit_human_node)

# Tools always route back to chat afterwards.
graph_builder.add_edge("tools", "chatbot")

# Start the conversation with the chatbot.
graph_builder.add_edge(START, "chatbot")

# Compile the graph for the DevBot.
chat_graph = graph_builder.compile()


# The default recursion limit for traversing nodes is set to allow for more complex interactions.
config = {"recursion_limit": 75}

# Initialize the state for the DevBot with an empty message history.
#state = chat_graph.invoke({"messages": []}, config)
