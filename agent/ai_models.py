import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

llm_provider = Literal["qwen", "ollama"]

def get_llm(llm:llm_provider, size:Literal['small', 'large'], temperature:float):

    if llm == "qwen":
        if size == "small":
            return ChatOpenAI(model="qwen-turbo", 
                              api_key=os.getenv('DASHSCOPE_API_KEY'),
                              base_url=os.getenv('DASHSCOPE_BASE_URL'),
                              temperature=temperature)
        elif size == "large":
            return ChatOpenAI(model="qwen-plus", 
                              api_key=os.getenv('DASHSCOPE_API_KEY'),
                              base_url=os.getenv('DASHSCOPE_BASE_URL'),
                              temperature=temperature)
    elif llm == "ollama":
        return ChatOllama(model="deepseek-r1:14b",
                          temperature=temperature)
    
