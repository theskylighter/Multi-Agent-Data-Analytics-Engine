import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from langchain.messages import AIMessage, HumanMessage
from utils.llm_pick import pick_llm
from Models.schema import AgentSchema, JudgeSchema
from utils.database import DatabaseUtil
from langgraph.graph import StateGraph , START , END
DATABASE_URL = os.environ.get("DATABASE_URL")

# --------------------------- AI Agent Code-------------------------------
# function== nodes
 
def curate_question(state:AgentSchema)-> AgentSchema:
    user_question = state.user_question
    llm_obj= pick_llm("low")
     
    response = llm_obj.invoke(f"Curate the following question for SQL query generation:{user_question} ").content
    state.curated_ques = response
    state.messages=  state.messages+ [HumanMessage(content=f"Curated Question: {response}")]
    return state

def prompt_query_content(state:AgentSchema)->AgentSchema :
    curated_question = state.curated_ques

    obj=DatabaseUtil(DATABASE_URL)
    schema_info =  obj.schema_details("public")

    # Constructing the prompt query for the agent to generate the SQL query
    prompt = f"""
    You are an SQL analyst agent. Your task is to convert the user's natural language 
    query into Postgres SQL query that can be executed on the database. You are provided 
    with the user's original query and the schema details of the database, including
    table names, column names, data types, and sample data for each table so that 
    you can understand the structure of the database and generate an accurate SQL query.
    Unless user explicitly asks for specific number of rows, always limit the output to 10 rows.
    Note - Just generate the SQL query without any explanation or additional text because
    this query will be executed directly on the database. So, the output should be SQL
    ready to be executed without any modifications.  
    
    User's Curated Query: {curated_question}

    Database Schema Details:
    {schema_info}
    
    """    

    state.prompt_query_context = prompt
    
    return state

# generate SQL query node
def generate_sql_query(state:AgentSchema)->AgentSchema:
    prompt  = state.prompt_query_context
    
    llm = pick_llm("medium")
    raw = llm.invoke(prompt).content.strip()
    
    # Strip markdown code fences if the model wraps output in ```sql ... ```
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]           # drop the opening ```sql line
        raw = raw.rsplit("```", 1)[0].strip()  # drop the closing ```
    
    state.generated_sql_query = raw
    return state

def is_safe_sql(state: AgentSchema) -> AgentSchema:
    sql_query = state.generated_sql_query
    llm_judge = pick_llm("medium").with_structured_output(JudgeSchema, method="json_mode")
    
    prompt = f"""You are a SQL security judge. Determine if the following SQL query is safe.

A safe query ONLY reads data (SELECT statements). It must NOT contain any of:
INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, EXEC, or any other data-modifying commands.

Respond with a JSON object matching the required schema:
- "answer": "Yes" if safe, "No" if unsafe
- "comments": brief explanation

SQL query to evaluate:
{sql_query}"""
    
    response = llm_judge.invoke(prompt).model_dump()
    state.is_safe = response["answer"]
    state.comments = response.get("comments", "")
    return state

def cancelled_sql(state:AgentSchema)->AgentSchema:
    comments = state.comments
    state.final_answer = f"The SQL query was deemed unsafe to execute. The reason provided by the judge is : {comments}. Therefore, the SQL query execution has been cancelled to ensure data security."
    state.messages = state.messages + [AIMessage(content=f"{state.final_answer}")]
    return state

def execute_sql(state:AgentSchema)->AgentSchema:
    sql_query = state.generated_sql_query
    
    obj=DatabaseUtil(DATABASE_URL)
    
    state.sql_query_execution_result = obj.execute_sql(sql_query)
    return state

def represent_final_answer(state:AgentSchema)->AgentSchema:
    sql_result = state.sql_query_execution_result
    llm = pick_llm("low")
    prompt = f"""
    You are an SQL analyst agent. Your task is to provide a final answer to the user's original question. The final answer should be clear, concise, and directly address the user's query. avoid inclding any SQL queries or technical details in the final answer. The final answer should be in a user friendly format that is easy to understand. If the execution result is empty, or does not provide a clear answer to the user's question, explain this in the final answer. Here is the execution result of the SQL query: {sql_result} \n
    Here is the user's original question: {state.user_question}
    """
    state.final_answer= llm.invoke(prompt).content
    state.messages = state.messages + [AIMessage(content= f"{state.final_answer}")]
    return state

# ---------------------------------------GRAPH Building--------------------------------------------
sql_agent_graph = StateGraph(AgentSchema)

#Nodes
sql_agent_graph.add_node("curate_question", curate_question)
sql_agent_graph.add_node("prompt_query_content", prompt_query_content)
sql_agent_graph.add_node("generate_sql_query", generate_sql_query)
sql_agent_graph.add_node("is_safe_sql", is_safe_sql)
sql_agent_graph.add_node("cancelled_sql", cancelled_sql)
sql_agent_graph.add_node("execute_sql", execute_sql)
sql_agent_graph.add_node("represent_final_answer", represent_final_answer)

#Edges
sql_agent_graph.add_edge(START,"curate_question")
sql_agent_graph.add_edge("curate_question","prompt_query_content")
sql_agent_graph.add_edge("prompt_query_content","generate_sql_query")
sql_agent_graph.add_edge("generate_sql_query","is_safe_sql")
#Conditionl Edge function
def is_safe_sql_edge(state:AgentSchema)->str:
    if state.is_safe == "Yes":
        return "execute_sql"
    else:
        return "cancelled_sql"

sql_agent_graph.add_conditional_edges("is_safe_sql", is_safe_sql_edge)
sql_agent_graph.add_edge("cancelled_sql",END)
sql_agent_graph.add_edge("execute_sql","represent_final_answer")
sql_agent_graph.add_edge("represent_final_answer",END)

if __name__ == "__main__":
    # Example usage of the SQL analyst agent graph
    input_schema = AgentSchema(
        messages=[],
        user_question="What are the different kinds of payments we have in our system?",
        curated_ques="",
        prompt_query_context="",
        is_safe="No",
        comments="",
        generated_sql_query="",
        sql_query_execution_result="",
        final_answer=""
    )
# #compile 
    sql_analyst = sql_agent_graph.compile()
    sql_analyst_response = sql_analyst.invoke(input_schema)
    print(sql_analyst_response['messages'])  # Print the final output of the graph execution
    print("********************************")

    print(sql_analyst_response['generated_sql_query'])  # Print the generated SQL query

    print("********************************")

    print(sql_analyst_response['sql_query_execution_result'])  # Print the result of executing the SQL query

    print("********************************")

    print(sql_analyst_response['prompt_query_context'])  # Print the prompt query context