from dotenv import load_dotenv
import os
from langchain.tools import tool
from logger import log
import json
from fastapi import HTTPException
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain.messages import AIMessage
from datetime import datetime
from langsmith import traceable


#load env
load_dotenv()
api_key=os.getenv("GROQ_API_KEY")

schedule="schedule.json"


# create event tool

@tool
def create_event(title,duration_minutes=60):
    """add a new events"""   
    try:
        if os.path.exists(schedule) and os.path.getsize(schedule)>0:
            with open(schedule,'r') as file:
                schedules=json.load(file)
        else:
            schedules=[]
        todays_Date = datetime.now()
        isoformat_date = todays_Date.isoformat()
        event={'title':title,'time':isoformat_date,'duration_minutes':duration_minutes}
        schedules.append(event)
        with open(schedule,'w') as file:
            json.dump(schedules,file,indent=4)
                   
        log.info("Event created")  
        return f"Event created"    
    except Exception as e:
        log.error("Event not created")
        raise HTTPException(status_code=500,detail=f"error in create event {e}")
    
@tool
def get_events():
    """ show all events."""
    try:
        with open(schedule,'r') as file:
            get_event=json.load(file)
        result=" "
        date_str=datetime.now().strftime("%Y-%m-%d")

        for i,t in enumerate(get_event,start=1):
            result+=f"{i}.{t['title']+ date_str}"

        log.info("Show Events")
        return f"result{result}"
    
    except Exception as e:
        log.error("Events not found")
        raise HTTPException(status_code=500,detail=f"error in get_events{e}")
    

@tool
def check_availability(time,duration_minutes=60):
    """ask available slot """
    try:
        with open(schedule,'r') as file:
            schedules=json.load(file)
        

        
        
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"error in check_availability {e}")


@tool
def update_event(old_time,new_time):
    """update an events """
    try:
        with open(schedule,'r') as file:
            schedules=json.load(file)
        
        old_time=datetime.now().fromisoformat()
        new_time=datetime.now().isoformat()


    except Exception as e:
        log.error("Event not updated")
        raise HTTPException(status_code=500,detail=f"error in update_event {e}")
    
system_prompt=f"""
- you are  Scheduling Assistant.
- you are follow the below rules.

Rules:
1.if user asks create new events then call create_event tool,only respond  "Event created"
2.if you are show events or query schedule then call get_events.sorted by start time.
3.give answer polity and natural language.
4.if you are update events then call update_event tool.you are not delete or recreate events.
5.if user schedule multiple events then add one by one in json.

"""

model=ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key)

agent=create_agent(
    model=model,
    tools=[create_event,get_events,check_availability,update_event],
    system_prompt=system_prompt
)


# call agent
@traceable(name="tool_result")
def tool_result(query:str):
    try:  
        response=agent.invoke({'messages':[AIMessage(content=query)]})
        return response
    except Exception as e:
        log.error("tool_result is not callable")
        raise HTTPException(status_code=500,detail=f"error in tool_result {e}")