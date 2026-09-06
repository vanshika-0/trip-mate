from tool.tavily_tool import tavily_search
from tool.flight_tool import search_flights
from backend import run_travel_agent

# res=tavily_search("best hotels in india")
# ress=search_flights("I want to book a flight from delhi to mumbai on 5 september 2026")
# print(res)
# print(ress)
user_input = input("enter travel request:")
response = run_travel_agent(user_input = user_input , thread_id = "test_user")

print("flight results:",response) 


