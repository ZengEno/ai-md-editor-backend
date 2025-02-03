import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

llm_provider = Literal["qwen", "ollama", "deepseek", "aliyun_eas", "fireworks"]

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
    
    if llm == 'aliyun_eas':
        return ChatOpenAI(model=model, 
                          api_key=os.getenv('aliyun_eas_eno_ds_r1_qwen_32b_api_key'),
                          base_url=os.getenv('aliyun_eas_eno_ds_r1_qwen_32b_api_base'),
                          temperature=temperature)

    if llm == 'fireworks':
        return ChatOpenAI(model='accounts/fireworks/models/deepseek-r1', 
                          api_key=os.getenv('FIREWORKS_API_KEY'),
                          base_url=os.getenv('FIREWORKS_API_BASE'),
                          temperature=temperature)