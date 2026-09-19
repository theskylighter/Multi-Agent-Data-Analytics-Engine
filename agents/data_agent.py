import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from Models.schema import DataAgentSchema
from agents.etl_analyst import etl_analyst_graph
from agents.sql_analyst import sql_agent_graph
from utils.llm_pick import pick_llm

llm = pick_llm("medium")

etl_agent = etl_analyst_graph.compile()
sql_agent = sql_agent_graph.compile()


# ---------------------------- DATA AGENT GRAPH ---------------------------- #
def router_node(state: DataAgentSchema):
    if not state.messages:
        raise ValueError("No messages available to route.")

    message = state.messages[-1].content
    prompt = f"""
    Decide if this request belongs to SQL or ETL. Return valid JSON only.
    Format:
    {{"answer": "sql|etl", "comments": "short reason"}}

    Request:
    {message}
    """
    raw = llm.invoke(prompt).content.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    route_response_dict = json.loads(raw)
    state.route_response = str(route_response_dict.get("answer", "sql")).lower()
    state.comments = str(route_response_dict.get("comments", ""))
    return state


def etl_node(state: DataAgentSchema):
    if not state.messages:
        raise ValueError("No messages available for ETL.")

    message = state.messages[-1].content
    response = etl_agent.invoke({"messages": [HumanMessage(content=message)]})
    state.messages = list(response.get("messages", []))
    state.comments = "ETL workflow completed"
    return state


def sql_node(state: DataAgentSchema):
    if not state.messages:
        raise ValueError("No messages available for SQL.")

    message = state.messages[-1].content
    input_schema = {
        "messages": [HumanMessage(content=message)],
        "user_question": message,
        "curated_ques": "",
        "prompt_query_context": "",
        "generated_sql_query": "",
        "is_safe": "No",
        "comments": "",
        "sql_query_execution_result": "",
        "final_answer": "",
    }

    response = sql_agent.invoke(input_schema)
    state.messages = list(response.get("messages", []))
    state.comments = "SQL workflow completed"
    return state


def route_edge(state: DataAgentSchema) -> str:
    if state.route_response == "sql":
        return "sql_node"
    if state.route_response == "etl":
        return "etl_node"
    raise ValueError(f"Invalid route response: {state.route_response}")


data_agent_graph = StateGraph(DataAgentSchema)
data_agent_graph.add_node("router_node", router_node)
data_agent_graph.add_node("etl_node", etl_node)
data_agent_graph.add_node("sql_node", sql_node)
data_agent_graph.add_edge(START, "router_node")
data_agent_graph.add_conditional_edges(
    "router_node",
    route_edge,
    {
        "sql_node": "sql_node",
        "etl_node": "etl_node",
    },
)
data_agent_graph.add_edge("etl_node", END)
data_agent_graph.add_edge("sql_node", END)

data_agent = data_agent_graph.compile()


if __name__ == "__main__":
    response = data_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extract folder in the csv folder"
                )
            ],
            "route_response": "",
            "comments": "",
        }
    )

    print(response)
