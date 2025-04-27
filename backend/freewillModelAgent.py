import os
import requests
import json
from smolagents import CodeAgent, Tool, ChatMessage  # Ensure this library is correctly installed
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")

# Initialize Groq LLM
model = ChatGroq(
    temperature=0.1,
    model_name="mixtral-8x7b-32768",
    groq_api_key=GROQ_API_KEY
)

class GetWeatherTool(Tool):
    name = "get_weather"
    description = "Fetches real-time weather for a given city."
    inputs = {
        "city": {"type": "string", "description": "The name of the city to fetch weather for."}
    }
    output_type = "string"

    def forward(self, city: str) -> str:
        """Fetches weather data for a given city."""
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        
        try:
            response = requests.get(url).json()
            if "main" in response:
                return f"The temperature in {city} is {response['main']['temp']}°C with {response['weather'][0]['description']}."
            return "Weather data not found."
        except Exception as e:
            return f"Error fetching weather data: {e}"

class GetCryptoPriceTool(Tool):
    name = "get_crypto_price"
    description = "Fetches real-time cryptocurrency price."
    inputs = {
        "crypto": {"type": "string", "description": "The name of the cryptocurrency to fetch the price for."}
    }
    output_type = "string"

    def forward(self, crypto: str) -> str:
        """Fetches cryptocurrency price data."""
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd"
        
        try:
            response = requests.get(url).json()
            if crypto in response:
                return f"The current price of {crypto} is ${response[crypto]['usd']}."
            return "Crypto data not found."
        except Exception as e:
            return f"Error fetching crypto price: {e}"

class GetNewsTool(Tool):
    name = "get_news"
    description = "Fetches the latest news headlines."
    inputs = {}  # No inputs required
    output_type = "string"

    def forward(self) -> str:
        """Fetches top news headlines."""
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWSAPI_API_KEY}"
        
        try:
            response = requests.get(url).json()
            if "articles" in response:
                news = [f"{article['title']} - {article['source']['name']}" for article in response["articles"][:5]]
                return "\n".join(news)
            return "No news available."
        except Exception as e:
            return f"Error fetching news: {e}"

# ✅ Define Tools Correctly
tools = [GetWeatherTool(), GetCryptoPriceTool(), GetNewsTool()]

# ✅ Initialize Smol Agent with Tool Calling
agent = CodeAgent(model=model, tools=tools)

def smol_agent_chat(prompt: str) -> str:
    """Processes user prompt, calls LLM, triggers tool calls, and returns the final response."""
    try:
        # 🔹 Step 1: Ask the LLM how to respond
        llm_response = model.invoke([{"role": "user", "content": prompt}])

        # 🔹 Step 2: Check if the LLM suggests using a tool
        agent_response = agent.run(llm_response.content)

        # 🔹 Step 3: Process the response from the agent
        if isinstance(agent_response, ChatMessage):
            if isinstance(agent_response.content, list):  # Ensure response is properly formatted
                response_text = "\n".join(
                    msg["text"] for msg in agent_response.content if isinstance(msg, dict) and "text" in msg
                ).strip()
                return response_text if response_text else "No valid response generated."
        
            return str(agent_response.content)  # Convert to string if necessary


        elif isinstance(agent_response, dict):  # If response is a dictionary, check for system messages
            if "role" in agent_response and agent_response["role"] == "system":
                if isinstance(agent_response.get("content"), list):
                    extracted_texts = [
                        msg.get("text", "") for msg in agent_response["content"] if isinstance(msg, dict) and "text" in msg
                    ]
                    return "\n".join(extracted_texts).strip()
                return str(agent_response.get("content", "System message received."))

            return json.dumps(agent_response, indent=2)  # Pretty-print dict response

        elif isinstance(agent_response, list):  # If response is a list, join and return
            return "\n".join(map(str, agent_response))

        return str(agent_response)  # Convert any other response types to string
    
    except Exception as e:
        return f"Error generating response: {e}"

# 🔥 Example Usage
if __name__ == "__main__":
    user_input = input("Enter your query: ")
    response = smol_agent_chat(user_input)
    print("\n🤖 AI Response:\n", response)
