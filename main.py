
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tool_connector_ui import UiToolConnector

import openai
import anthropic
import chromadb
from chromadb.config import Settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Initialize ChromaDB client
chroma_client = chromadb.Client(Settings(
    persist_directory="./chroma_db"
))
collection = chroma_client.get_or_create_collection(name="demo_collection")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only; restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for API keys (for demo only)
api_keys = {
    "openai": None,
    "anthropic": None
}

class AuthRequest(BaseModel):
    client_id: str
    tenant_id: str

class ChatRequest(BaseModel):
    provider: str  # 'openai' or 'anthropic'
    model: str
    message: str


# Advanced: Automatic embedding generation and semantic search
class AddDocRequest(BaseModel):
    doc_id: str
    text: str

@app.post("/add_document")
def add_document_api(req: AddDocRequest):
    # Generate embedding using OpenAI
    if not api_keys["openai"]:
        raise HTTPException(status_code=400, detail="OpenAI API key not set")
    client = openai.OpenAI(api_key=api_keys["openai"])
    emb_response = client.embeddings.create(
        input=req.text,
        model="text-embedding-3-small"  # or another embedding model
    )
    embedding = emb_response.data[0].embedding
    collection.add(
        ids=[req.doc_id],
        documents=[req.text],
        embeddings=[embedding]
    )
    return {"status": "success"}

class QueryRequest(BaseModel):
    query: str
    n_results: int = 3

@app.post("/semantic_search")
def semantic_search_api(req: QueryRequest):
    # Generate embedding for query
    if not api_keys["openai"]:
        raise HTTPException(status_code=400, detail="OpenAI API key not set")
    client = openai.OpenAI(api_key=api_keys["openai"])
    emb_response = client.embeddings.create(
        input=req.query,
        model="text-embedding-3-small"
    )
    query_embedding = emb_response.data[0].embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=req.n_results
    )
    return results
def get_keys():
    return {
        "openai_set": api_keys["openai"] is not None,
        "anthropic_set": api_keys["anthropic"] is not None
    }

@app.post("/list_onedrive_files")
def list_onedrive_files(auth: AuthRequest):
    try:
        connector = UiToolConnector(auth.client_id, auth.tenant_id)
        result = connector.execute("list_onedrive_files", {})
        return result.summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_inference(req: ChatRequest):
    try:
        if req.provider == "openai":
            if not api_keys["openai"]:
                raise HTTPException(status_code=400, detail="OpenAI API key not set")
            client = openai.OpenAI(api_key=api_keys["openai"])
            response = client.chat.completions.create(
                model=req.model,
                messages=[{"role": "user", "content": req.message}]
            )
            return {"response": response.choices[0].message.content}
        elif req.provider == "anthropic":
            if not api_keys["anthropic"]:
                raise HTTPException(status_code=400, detail="Anthropic API key not set")
            client = anthropic.Anthropic(api_key=api_keys["anthropic"])
            response = client.messages.create(
                model=req.model,
                max_tokens=512,
                messages=[{"role": "user", "content": req.message}]
            )
            return {"response": response.content}
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
