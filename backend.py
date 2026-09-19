import os 
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict, Annotated
import operator
import uuid

# --- MongoDB Checkpointer Imports ---
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from langgraph.checkpoint.mongodb import MongoDBSaver

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq
from tool.tavily_tool import tavily_search
from tool.flight_tool import search_flights


def get_database_url():
    # Fetch Mongo connection string (e.g., mongodb+srv://username:password@cluster.mongodb.net/...)
    database_url = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "MONGODB_URI is missing. Add your MongoDB connection string to .env"
        )

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your .env file.")


# =========================
# LLM
# =========================
GROQ_MODEL = os.getenv("GROQ_MODEL")
llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY
)


# =========================
# State
# =========================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

class bro(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

# =========================
# Flight Agent
# =========================

def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content="Flight results fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# =========================
# Hotel Agent
# =========================

def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# =========================
# Itinerary Agent
# =========================

def itinerary_agent(state: TravelState):
    prompt = f"""
Create a complete travel itinerary.

User Query:
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results:
{state['hotel_results']}

Make the itinerary practical, budget-aware, and easy to follow.
"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are an expert travel planner."),
            HumanMessage(content=prompt)
        ])
    except Exception as error:
        response = AIMessage(
            content=(
                "Automatic itinerary generation is unavailable right now "
                f"({type(error).__name__}). Use the flight and hotel results "
                "above to complete the plan."
            )
        )

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# =========================
# Final Response Agent
# =========================

def final_agent(state: TravelState):
    final_prompt = f"""
Generate the final travel response for the user.

User Request:
{state['user_query']}

Flights:
{state['flight_results']}

Hotels:
{state['hotel_results']}

Itinerary:
{state['itinerary']}

FORMATTING AND STYLE REQUIREMENTS:
- Use Markdown headers (`##`) for each section title.
- Separate every section with a clear blank line / empty line.
- Use bullet points (`-`) or numbered lists where appropriate instead of dense paragraphs.
- Keep the overall output neat, well-organized, and highly readable.

Format the final answer using these exact sections (each separated by an empty line):

## 1. Trip Summary

## 2. Flight Information

## 3. Hotel Suggestions

## 4. Day-by-Day Itinerary

## 5. Estimated Budget

## 6. Final Recommendations

Important:
- Be clear and practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Keep the response useful for real travel planning.
"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a professional AI travel booking assistant."),
            HumanMessage(content=final_prompt)
        ])
    except Exception as error:
        response = AIMessage(
            content=(
                f"Trip request: {state['user_query']}\n\n"
                f"Flight information:\n{state['flight_results']}\n\n"
                f"Hotel information:\n{state['hotel_results']}\n\n"
                f"Itinerary:\n{state['itinerary']}\n\n"
                "AI formatting is temporarily unavailable."
            )
        )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# =========================
# Build Graph
# =========================

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# =========================
# MongoDB Checkpointer Setup
# =========================
travel_graph = None


def get_travel_graph():
    """Create the MongoDB-backed graph only when it is first used."""
    global travel_graph

    if travel_graph is None:
        try:
            mongodb_uri = get_database_url()
            mongodb_client = MongoClient(
                mongodb_uri,
                connect=False,
                serverSelectionTimeoutMS=int(
                    os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
                ),
            )
            checkpointer = MongoDBSaver(
                client=mongodb_client,
                db_name=os.getenv("MONGODB_DB_NAME", "travel_agent_db"),
            )
        except PyMongoError as error:
            raise RuntimeError(
                "MongoDB connection failed. Check MONGODB_URI, confirm the "
                "cluster exists, and allow your IP address in MongoDB Atlas."
            ) from error

        travel_graph = graph.compile(checkpointer=checkpointer)

    return travel_graph


# =========================
# Function for FastAPI
# =========================

def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = get_travel_graph().invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }
