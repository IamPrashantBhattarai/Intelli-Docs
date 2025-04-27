import os
from langchain_groq import ChatGroq
from langchain.schema import AIMessage, HumanMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq LLM
llm = ChatGroq(
    temperature=0.1, 
    model_name="mixtral-8x7b-32768", 
    groq_api_key=GROQ_API_KEY
)

def chat_with_groq(prompt: str) -> str:
    """Generates a response from the Groq LLM using LangChain."""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content  # Extract and return response text
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage
# if __name__ == "__main__":
#     user_prompt = input("Enter your prompt: ")
#     response = chat_with_groq(user_prompt)
#     print("\n💬 Groq LLM Response:\n", response)
