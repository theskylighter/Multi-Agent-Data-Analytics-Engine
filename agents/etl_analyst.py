import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))  
from utils.llm_pick import pick_llm
from utils.etl_tools import ETLTools
from Models.schema import ETLAgentSchema
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph , START , END
from langchain.tools import tool
from langchain_openai import ChatOpenAI

# --------------------------------------ETL Agent Code--------------------------------------#

@tool
def extract_load_tool(url:str, output_folder:str,  file_type:str)->str:
    """
    This function is a tool that extracts data from a given URL and saves it to a specified output folder with the given file name and type.
    
    Args:
        url (str): The URL from which to extract data.
        output_folder (str): The folder where the extracted data will be saved.
        file_type (str): The type of the file to save the extracted data as (e.g., 'csv', 'json', 'parquet').
    
    Returns:
        str: A message indicating the success or failure of the extraction and loading process.
    """
    etl_tool = ETLTools()
    return etl_tool.extract_load(url, output_folder, file_type)
     
@tool
def transform_load_tool(input_file_path:str, output_folder:str,output_format:str, user_question:str)->str:
    """
    This function is a tool that transforms data from a given input file and saves it to a specified output folder with the given output format.
    
    Args:
        input_file_path (str): The path to the input file containing the data to be transformed.
        output_folder (str): The folder where the transformed data will be saved.
        output_format (str): The format in which to save the transformed data (e.g., 'csv', 'json', 'parquet').
    
    Returns:
        str: A message indicating the success or failure of the transformation and loading process.
    """
    etl_tool = ETLTools()
    print("input_file_path:", input_file_path)
    print("output_folder:", output_folder)
    print("output_format:", output_format)
    print("user_question:", user_question)

    top_3_rows = etl_tool.transform_load_context(input_file_path, output_folder, output_format)
    print("\n\t  Transform_load_tool \t Top_3_rows : ", top_3_rows)

    if isinstance(top_3_rows, str):
        return top_3_rows

    available_columns = list(top_3_rows.columns)
    required_columns = ["base_experience", "height"]
    missing_columns = [
        column for column in required_columns
        if column not in available_columns
    ]
    if missing_columns:
        return (
            "Cannot perform the requested transformation. "
            f"Missing columns: {missing_columns}. "
            f"Available columns: {available_columns}. "
            "No additional data was fetched."
        )

    llm= pick_llm("high")

    prompt = f"""
        You are a Python Data Analyst who uses Pandas to analyse data.
        You need to provide only the Pandas Code that will help to perform the right ETL operations as per the user question or request.
        Do not provide any explanation or additional text. The code should be ready to run without any modifications in a Python environment with Pandas installed.
        Don't write anything else than Pandas Code. \n

        Create the Pandas Dataframe from the data stored in the file : {input_file_path} and write the code to transform & save the data at {output_folder}.
        Here's the user's question : {user_question}\n
        Here's the context of the data you will be analyzing: {top_3_rows}\n
        """
    response= llm.invoke(prompt).content
    print(f"LLM Response : {response}")
    
    # optional cleaning of the response to remove any code block formatting
    pandas_code = response.strip().strip("```").strip().lstrip("python").strip()

    results = etl_tool.execute_code(pandas_code)

    if results.startswith("Error executing code:"):
        return results

    return (
        f"The data was transformed and stored at "
        f"{output_folder} in format {output_format}.\n\n"
        f"Execution result: {results}"
    )

tools = [extract_load_tool, transform_load_tool]

# -------------------------------AGENT GRAPH--------------------------------------#
def llm_node(state:ETLAgentSchema):

    llm = pick_llm("medium")
    llm_bind = llm.bind_tools(tools)

    prompt = f"""
    You are a Python Data Analyst who has access to tools that can
    extract, transform and load data.

    Chat history:
    {state.messages}
    """

    final_answer = llm_bind.invoke(prompt)

    return {"messages": [final_answer]}
def tool_node(state:ETLAgentSchema):
    """
    This node is responsible for invoking the appropriate tool based on the user's question and the last message in the conversation. It checks if the last message is a ToolMessage, and if so, it extracts the tool name and input, invokes the tool, and appends the tool's output to the conversation history."""
    tools_by_name = {tool.name: tool for tool in tools}
    tool_messages = []

    for tool_call in state.messages[-1].tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        observation = selected_tool.invoke(tool_call["args"])

        tool_messages.append(
            ToolMessage(
                content=observation,
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_messages}


# Nodes & Edges for the ETL Agent Graph
etl_analyst_graph = StateGraph(ETLAgentSchema)
etl_analyst_graph.add_node("llm_node", llm_node)
etl_analyst_graph.add_node("tool_node", tool_node)
etl_analyst_graph.add_edge(START, "llm_node")
etl_analyst_graph.add_edge("tool_node", "llm_node")

def is_tool_call(state:ETLAgentSchema)->str:
    last_message = state.messages[-1]
    tool_calls = last_message.tool_calls
    if tool_calls:
        return "tool_node"
    else:
        return "END"

etl_analyst_graph.add_conditional_edges(
    "llm_node", is_tool_call,
    {
        "tool_node": "tool_node",
         "END": END
    }
)


if __name__ == "__main__":
    # llm_bind = pick_llm("medium").bind_tools(tools)
    # print(llm_bind.invoke("I want to extract the data from the API endpoint https://api.example.com/data and save it as a CSV file in the folder /data/extract."))
    
    etl_analyst =etl_analyst_graph.compile()

    # from IPython.display import display, Image
    # img = Image(etl_analyst.get_graph().draw_mermaid_png())
    # with open("etl_analyst_graph.png","wb") as f:
    #     f.write(img.data)

    # response = etl_analyst.invoke(
    #     {"messages":[HumanMessage(content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon/' and save it as a CSV file in the folder data/extract.")]
    #     }
    # )
    # print(response)

    # {'messages': [HumanMessage(content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon/' and save it as a CSV file in the folder data/extract.", additional_kwargs={}, response_metadata={}), AIMessage(content="I'll extract the data from the PokéAPI endpoint and save it as a CSV file in the `data/extract` folder right away!", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 28, 'prompt_tokens': 1032, 'total_tokens': 1060, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 'model_provider': 'openai', 'model_name': 'auto','system_fingerprint': None, 'id': 'chatcmpl-1789846982408', 'finish_reason': 'tool_calls', 'logprobs':None}, id='lc_run--01a0bb31-8714-7c82-a36f-bcc4a17ee1d2-0', tool_calls=[{'name': 'extract_load_tool', 'args': {'url': 'https://pokeapi.co/api/v2/pokemon/', 'output_folder': 'data/extract', 'file_type': 'csv'}, 'id': 'tooluse_gLKSsdyMOU4BSaHM20fhdv', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 1032, 'output_tokens': 28, 'total_tokens': 1060, 'input_token_details': {}, 'output_token_details': {}}), ToolMessage(content=' Data successfully extracted and saved to /home/shivam/sandbox/Dataagent/data/extract/Extracted_data.csv', tool_call_id='tooluse_gLKSsdyMOU4BSaHM20fhdv'), AIMessage(content="The extraction is done. The PokéAPI data has been saved to `data/extract/Extracted_data.csv`.\n\nNow, what would you like to do with this data? For example, I can:\n- **Transform** it — clean, filter, reshape, or enrich the data\n- **Analyze** it — summarize stats, find patterns, answer specific questions\n- **Load** it into a different format — like JSON or Parquet\n\nWhat's next?", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 94, 'prompt_tokens': 1044, 'total_tokens': 1138, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 'model_provider': 'openai', 'model_name': 'auto', 'system_fingerprint': None, 'id': 'chatcmpl-1789846985823', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--01a0bb31-9445-7f42-b9c4-7f8850c79a78-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 1044, 'output_tokens': 94, 'total_tokens':1138, 'input_token_details': {}, 'output_token_details': {}})]}
    
    response = etl_analyst.invoke(
        {"messages":[HumanMessage(content="I want to transform the data in the file 'data/extract/Extracted_data.csv' and save it as a JSON file in the folder 'data/transform'. The transformation should filter the data to include only Pokémon with a base experience greater than 200 and sort them by their height in descending order.")]
        })
    print(response)