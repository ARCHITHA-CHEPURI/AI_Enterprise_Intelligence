import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sys

# Ensure scripts can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.rag_pipeline import retrieve, generate_answer_with_metrics

app = FastAPI(title="RAG Chatbot API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class QueryRequest(BaseModel):
    query: str

class Source(BaseModel):
    source: str
    chunk_id: str
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    accuracy: float
    precision: float
    confidence: float

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    try:
        query = request.query
        # 1. Retrieve context
        context_chunks = retrieve(query)
        
        # 2. Generate answer with metrics
        if not context_chunks:
            return QueryResponse(
                answer="I couldn't find any relevant information in the documents.", 
                sources=[],
                accuracy=0.0,
                precision=0.0,
                confidence=0.0
            )
            
        answer, context, acc, prec, conf = generate_answer_with_metrics(query, context_chunks)
        
        # 3. Format sources
        sources = []
        for chunk in context:
            sources.append(Source(
                source=chunk.get('source', 'Unknown'),
                chunk_id=chunk.get('chunk_id', ''),
                text=chunk.get('text', '')
            ))
            
        return QueryResponse(
            answer=answer, 
            sources=sources,
            accuracy=acc,
            precision=prec,
            confidence=conf
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def get_file(filename: str):
    # Security: Prevent traversing up directories
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
         raise HTTPException(status_code=400, detail="Invalid filename")

    # Search for the file in the Data directory recursively
    # This assumes unique filenames across directories or just takes the first found
    search_path = os.path.join("Data", "**", filename)
    files = glob.glob(search_path, recursive=True)
    
    if files:
        return FileResponse(files[0])
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
