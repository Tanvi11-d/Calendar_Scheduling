from fastapi import FastAPI,HTTPException
from utils import *
from logger import log

app=FastAPI()

@app.get("/")
def health():
    return {"status":"Ok"}


@app.post("/query/")
def get_schedule(query:str):
    try:
        result=tool_result(query)
        answer=result.get('messages')[-1].content
        return {"answer":answer}
     
    except Exception as e:
        log.error("error in get_schedule")
        raise HTTPException(status_code=500,detail=f"error in get_schedule {e}")