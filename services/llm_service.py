from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API")

def build_context(chunks: List[dict]) -> str:
      context = ""
      for chunk in chunks:
            context+= f"File: {chunk['metadata']['file_path']} | Reference: {chunk['content']} \n\n"
        
      return context
            

def call_llm(question: str, context: str) -> str:
      client = genai.Client(api_key=GEMINI_KEY)
      response = client.models.generate_content(
        model="gemini-2.5-flash-lite", contents=f"Context:{context} Question:{question}",
          config=types.GenerateContentConfig( system_instruction="You are a code assistant. Answer based on the code context provided.")
        )
      return response.text
