import os
from openai import OpenAI

LLM_LITE_TOKEN = os.getenv("LLM_LITE_TOKEN")
LLM_LITE_URL = os.getenv("LLM_LITE_URL")

def get_llm_client():
    client = OpenAI(
        api_key=LLM_LITE_TOKEN,
        base_url=LLM_LITE_URL
    )
    return client

def get_llm_response(llm_client, prompt: str) -> str:
    response = llm_client.responses.create(
        model="gpt-5",
        instructions="You are a helpful assistant specializing in sensor data analysis.",
        input=prompt,
    )
    return response.output_text