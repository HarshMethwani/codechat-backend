from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API")

def build_context(chunks: List[dict]) -> str:
      context = ""
      for chunk in chunks:
            context+= f"File: {chunk['metadata']['file_path']} | Reference: {chunk['content']} \n\n"
        
      return context
            

def call_llm(question: str,history:List[dict], context: str) -> str:
      client = genai.Client(api_key=GEMINI_KEY)
      messages = []
      if history:
            for msg in history:
                  messages.append({
                        "role":msg['role'],
                        "parts":[{"text":msg["content"]}]
                  })
      
      messages.append({"role":"user","parts":[{"text":f"Context:{context} Question:{question}"}]})
      response = client.models.generate_content(
        model="gemini-2.5-flash-lite", contents=messages,
          config=types.GenerateContentConfig( system_instruction="You are a helpful code assistant. Consider the conversation history when responding. Use the provided code context to answer code questions.")
        )
      return response.text


def call_llm_stream(question: str,history:List[dict], context: str,sources:List[dict]) -> str:
      client = genai.Client(api_key=GEMINI_KEY)
      messages = []
      if history:
            for msg in history:
                  messages.append({
                        "role":msg['role'],
                        "parts":[{"text":msg["content"]}]
                  })
      
      messages.append({"role":"user","parts":[{"text":f"Context:{context} Question:{question}"}]})
      response = client.models.generate_content_stream(
        model="gemini-2.5-flash-lite", contents=messages,
          config=types.GenerateContentConfig( system_instruction="You are a helpful code assistant. Consider the conversation history when responding. Use the provided code context to answer code questions.")
        )
      yield f"data: {json.dumps({'type':'sources','data':sources})}\n\n"
      for chunk in response:
            yield f"data: {json.dumps({'type':'chunk','text':chunk.text})}\n\n"
     
      yield f"data: {json.dumps({'type':'done'})}\n\n"