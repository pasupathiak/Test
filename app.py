from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import ForeignKey, String, create_engine, Column, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from datetime import datetime
import redis
from database_session import get_db
from user_chat_service import get_ai_response
from db_connectivity_service import processAnalitics
from handle_knowledge_base import handle_knowledge_base
from table_structure_service import update_table_structure

# FastAPI App Setup
app = FastAPI(title="Vox AI Assistant", description="AI-powered database query and conversation assistant")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Initialize the embedding model
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

@app.put("/api/ai/update_kb/{xt_id}")
async def process_knowledge_base(xt_id: str, db: Session = Depends(get_db)):
    try:
        handle_knowledge_base(embedding_model, xt_id, db)
        return {"content": "Knowledge Base Successfully updated", "status": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Pydantic Models for Request Validation
class ChatRequest(BaseModel):
    tenant_id: str
    message: str

# Chat API Endpoint
@app.post("/api/ai/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):    
    user_message = request.message
    xt_vox_id = request.tenant_id
    try:
        ai_response = get_ai_response(user_message, embedding_model, xt_vox_id, db)
        return {"response": ai_response, "status": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UserNotFound(Exception):
    def __init__(self, xt_vox_id, msg="User Not Found"):
        self.xt_vox_id = xt_vox_id
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.xt_vox_id} -> {self.msg}'
    

class NoDataBaseException(Exception):
    def __init__(self, xt_vox_id, msg=f"No databse found for this user:"):
        self.xt_vox_id = xt_vox_id
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.xt_vox_id} -> {self.msg}'


# Exception Handlers
@app.exception_handler(UserNotFound)
async def user_not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": f"{exc.xt_vox_id} {exc.msg}"}
    )

@app.exception_handler(NoDataBaseException)
async def no_database_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": f"{exc.msg} {exc.xt_vox_id}"}
    )

class AnalyticsRequest(BaseModel):
    tennent_id: str
    message: str
    # dbStructure: str = None

@app.post('/api/ai/db-query')
async def processDatabaseRequest(request : AnalyticsRequest, db: Session = Depends(get_db)):
    try:
        tennent_id = request.tennent_id
        user_message = request.message
        Db_structure = redis_client.get(f"Db_structure_{tennent_id}")

        if Db_structure is None:
            raise HTTPException(status_code=404, detail=str("No database Structure Found"))

        imageString, queryResult = processAnalitics(tennent_id, user_message, Db_structure, db)
        return {"responseMessage": imageString, "resultData": queryResult, "status": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put('/api/ai/update-table-structure/{xt_id}')
async def updateTableStructure(xt_id: str, db: Session = Depends(get_db)):
    try:
        update_table_structure(redis_client, xt_id, db)
        return {"content": "Successfully updated"}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)