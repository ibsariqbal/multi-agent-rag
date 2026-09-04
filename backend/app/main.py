import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .models import ChatRequest, ChatResponse, Citation, DocumentInfo
from .services import DocumentParser, VectorStore
from .graph import RagGraph

settings = get_settings()
app = FastAPI(title="Multi-Agent RAG API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
store = VectorStore()
rag = RagGraph(store)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "demo" if settings.demo_mode else "pinecone"}

@app.get("/api/documents", response_model=list[DocumentInfo])
def documents():
    return list(store.documents.values())

@app.post("/api/documents", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...), category: str = Form("general")):
    data = await file.read()
    if len(data) > settings.max_file_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_file_mb} MB")
    try:
        pages = DocumentParser.parse(file.filename or "document.txt", data)
        return store.add(file.filename or "document.txt", pages, category)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    if not store.delete(doc_id):
        raise HTTPException(404, "Document not found")
    return {"deleted": True}

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = rag.invoke(request.question, [m.model_dump() for m in request.history], request.document_ids)
    citations = [Citation(number=i, document_id=c.metadata["document_id"], filename=c.metadata["filename"], page=c.metadata.get("page"), excerpt=c.text[:260], score=round(float(c.score), 3)) for i, c in enumerate(result["chunks"], 1)]
    return ChatResponse(answer=result["answer"], agent=result["route"], conversation_id=request.conversation_id or str(uuid.uuid4()), citations=citations)

