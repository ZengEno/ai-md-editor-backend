import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

llm_provider = Literal["qwen", "ollama", "deepseek"]

def get_llm(llm:llm_provider, model:str, temperature:float):

    if llm == "qwen":
        return ChatOpenAI(model=model, 
                            api_key=os.getenv('DASHSCOPE_API_KEY'),
                            base_url=os.getenv('DASHSCOPE_BASE_URL'),
                            temperature=temperature)

    if llm == "deepseek":
        return ChatOpenAI(model=model, 
                            api_key=os.getenv('DEEPSEEK_API_KEY'),
                            base_url=os.getenv('DEEPSEEK_BASE_URL'),
                            temperature=temperature)

    if llm == "ollama":
        return ChatOllama(model="deepseek-r1:14b",
                          temperature=temperature)
    
