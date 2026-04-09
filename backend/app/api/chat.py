from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import time
import os

# Get current working directory
current_dir = os.getcwd()

print("Current Directory:", current_dir)


from .rag.pipeline import Pipeline
from .rag.ingestor import Ingestor

pipeline = Pipeline()
ingestor = Ingestor()


router = APIRouter()

# -------------------------
# Non-WebSocket endpoint
# -------------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    query: str
    answer: str

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    dummy_answer = f"This is a dummy response for: '{request.query}'"
    return ChatResponse(query=request.query, answer=dummy_answer)

# -------------------------
# WebSocket endpoint
# -------------------------

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            dummy_answer = f"This is a dummy WS response for: '{data}'"
            await websocket.send_text(dummy_answer)
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket")

# -------------------------
# Streaming endpoint (SSE)
# -------------------------
async def async_real_stream_generator(query: str):
    import json
    import httpx
    import asyncio
    
    try:
        # Run synchronous parts in threadpool to not block the loop
        loop = asyncio.get_event_loop()
        standalone_query = await loop.run_in_executor(None, pipeline._generate_standalone_query, query)
        context = await loop.run_in_executor(None, pipeline._retrieve_context, standalone_query)
        from .rag.prompts import get_chat_prompt
        prompt = get_chat_prompt(query, history=pipeline.history, context=context)

        payload = {
            "model": pipeline.llm.model_name,
            "messages": prompt,
            "temperature": pipeline.llm.temperature,
            "max_tokens": pipeline.llm.max_tokens,
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        if pipeline.llm.api_key:
            headers["Authorization"] = f"Bearer {pipeline.llm.api_key}"

        full_response = ""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", pipeline.llm.api_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        data_str = chunk[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    text_chunk = delta['content']
                                    full_response += text_chunk
                                    safe_chunk = text_chunk.replace("\n", "\\n")
                                    yield f"data: {safe_chunk}\n\n"
                                    await asyncio.sleep(0.03)  # Visual ticker delay
                        except json.JSONDecodeError:
                            continue

        await loop.run_in_executor(None, pipeline._update_history, query, full_response)
            
    except Exception as e:
        yield f"data: I encountered an error: {str(e)}\n\n"
        
    yield "data: [DONE]\n\n"

@router.get("/chat/stream", tags=["Chat"])
async def chat_stream(query: str):
    """
    Stream chatbot response in real-time using SSE.
    Example: /api/chat/stream?query=Hello
    """
    return StreamingResponse(
        async_real_stream_generator(query), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )



def run_ingestion_task():
    """Wrapper for background ingestion with logging & error handling."""
    try:
        result = ingestor.ingest()
        # logger.info(f"Ingestion completed: {result}")
    except Exception as e:
        # logger.error(f"Ingestion failed: {e}")
        pass  # Avoid crashing background thread

# -------------------------
# Ingestor endpoint (GET with Background Task)
# -------------------------
@router.get("/ingest", tags=["Ingest"])
async def ingest_endpoint(background_tasks: BackgroundTasks):
    """
    Trigger ingestion in the background (non-blocking).
    Returns immediately with status message.
    """
    try:
        print(f'Ingestion request is accepted...')
        background_tasks.add_task(run_ingestion_task)
        return JSONResponse(
            content={"status": "started", "message": "Ingestion has been triggered and is running in the background."},
            status_code=202,  # Accepted, since processing is async
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")
    
