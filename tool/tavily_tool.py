from tavily import TavilyClient
import os 
import requests
from dotenv import load_dotenv
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


def tavily_search(query):
    if client is None:
        return "Hotel search unavailable: TAVILY_API_KEY is missing."

    try:
        response = client.search(
            query=query,
            max_results=5,
        )
    except requests.exceptions.RequestException as error:
        return (
            "Hotel search unavailable: network request failed "
            f"({type(error).__name__})."
        )
    except Exception as error:
        return f"Hotel search unavailable: {type(error).__name__}."

    results = []
    for i, r in enumerate(response["results"],1):
        title = r.get("title","Uknown")
        url= r.get("url","")
        snippet = r.get("content","").strip()
        if len(snippet) > 200:
            snippet = snippet[:300].rsplit(" ",1)[0] + "..."
        results.append(f"{i}. **{title}**\n {url}\n {snippet}")
    return "\n\n".join(results)
