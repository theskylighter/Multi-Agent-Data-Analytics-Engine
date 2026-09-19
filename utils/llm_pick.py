from langchain_openai import ChatOpenAI


def pick_llm(level:  str):
    """Picks the appropriate LLM based on the level of the question

    Args:
        level (str): The level of the question, can be "easy", "medium", "hard")
        
    Returns:
        str: The name of the lLM to be used
    """
    if level.lower()=="low":
        llm_client= ChatOpenAI(model="auto/cheap")
    elif level.lower()=="medium":
        llm_client= ChatOpenAI(model="auto")
    elif level.lower()=="high":
        llm_client= ChatOpenAI(model="auto/coding") 
    else:
        raise ValueError(f"Unsupported Level : {level}")
    
    return llm_client
# llm_obj=pick_llm("medium")
# print(llm_obj.invoke("What is the capitol of France"))

