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
def create_event(title:str,time,duration_minutes=60):
    """create a new events."""   
    try:
        try:
            dt=datetime.fromisoformat(time)
        except:
            dt=datetime.strftime(time,"%d-%B-%Y %I%p")
        isoformat_date=dt.isoformat()

        if os.path.exists(schedule) and os.path.getsize(schedule)>0:
            with open(schedule,'r') as file:
                schedules=json.load(file)
            
        else:
            schedules=[]

        for i in schedules:
            if i["time"]==isoformat_date and i["title"].lower()==title.lower() and i["duration_minutes"]==duration_minutes:
                return "Event already exists"
            
        event={'title':title,'time':isoformat_date,'duration_minutes':duration_minutes}
        schedules.append(event)
        with open(schedule,'w') as file:
            json.dump(schedules,file,indent=4)
                   
        log.info("Event created")  
        return f"{title} at {time}"
        
    except Exception as e:
        log.error("Event not created")
        raise HTTPException(status_code=500,detail=f"error in create event {e}")
   
@tool
def get_events(date):
    """get event sorted by start time."""
    try:

        with open(schedule,'r') as file:
            get_event=json.load(file)

        result=[]
        date=datetime.now().strftime("%Y-%m-%d")

        print("date___",date)

        for i in get_event:
            if i["time"].startswith(date):
                result.append(i)

        print("get_event__",i)


        def get_item(item):
            return item["time"]
        result.sort(key=get_item)

        output=" "
        for i,t in enumerate(get_event,start=1):
            output+=f"{i}.{t["title"]} {t["time"]}\n"
        
        log.info("Show Events")
        print("output__",output)
        return output
    
    except Exception as e:
        log.error("Events not found")
        raise HTTPException(status_code=500,detail=f"error in get_events{e}")
    
@tool
def check_availability(time):
    """check time slot available or not.return available slot and tell next free slot when taken.""" 
    try:

        with open(schedule,'r') as file:
            schedules=json.load(file)
        for i in schedules:
            if i["time"]==time:
                return False
        log.info("slot available")
        return True
    
    except Exception as e:
        log.error("slot not available")
        raise HTTPException(status_code=500,detail=f"error in check_availability {e}")


@tool
def update_event(old_time,new_time):
    """update an existing events.Do not delete or recreate events."""
    try:
        
        with open(schedule,'r') as file:
            schedules=json.load(file)
            
        for i in schedules:
            if i["time"]==old_time:
                i["time"]=new_time

                with open(schedule,'w') as file:
                    json.dump(schedules,file,indent=4)
                return "event updated"

        log.info("event updated")
        return "event not updated"
        
    except Exception as e:
        log.error("Event not updated")
        raise HTTPException(status_code=500,detail=f"error in update_event {e}")
    
system_prompt=f"""
- You are Calendar Scheduling Assistant.
- you are follow the below rules.

Rules:

1.create events
- create a new events -> call create_event.
- If user not define start time of events then take anything start time for that day and default duration minutes is 60.
- if user give range of events then store in separatly.
- do not create duplicates events.
- if user give date of range events(example:- create schedule 1 april to 5 april),
    i)create separate event one by one with same time and title.
    
2.get events
- show events or query schedule -> call get_events.
- it sorted by start time and Default date is today.
- if you are show event sorted by start time.
- when you are show all events then return with number format.

3.check availability
- check slot available or not -> call check_availability.
- return which slot available and tell next free slot when taken.

4.update event
- update events -> call update_event.
- update existing event slot to new slots based on datetime.
- you are not delete or recreate events.

5.others
- keep answer polity,concise and natural language.
- Do not give extra information.
- Do not show which tool you used.
- Do not answer general knowledge questions.
- Do not hallucinate create events,check availability or update events.

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
        log.info("tool_result callable")
        return response
    except Exception as e:
        log.error("tool_result is not callable")
        raise HTTPException(status_code=500,detail=f"error in tool_result {e}")