import io, re, uuid
from dataclasses import dataclass
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from .config import get_settings

@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict
    score: float = 0.0

DEMO_DOCS = {
    "architecture.md": "The system uses LangGraph for stateful orchestration. A coordinator routes questions to technical, financial, or general retrieval agents. Pinecone stores OpenAI embeddings. FastAPI exposes upload and chat endpoints. AWS Lambda runs the API through Mangum.",
    "operations.md": "Answers must cite retrieved passages. Uploads accept PDF, DOCX, TXT and Markdown. Documents are split into overlapping chunks. Production deployments should store secrets securely, restrict CORS, add authentication, and monitor latency and retrieval quality.",
}

class DocumentParser:
    @staticmethod
    def parse(name: str, data: bytes):
        ext = name.lower().rsplit(".", 1)[-1]
        if ext == "pdf":
            return [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(io.BytesIO(data)).pages)]
        if ext == "docx":
            text = "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
            return [(None, text)]
        if ext in {"txt", "md"}:
            return [(None, data.decode("utf-8", errors="replace"))]
        raise ValueError("Supported formats: PDF, DOCX, TXT, MD")

class VectorStore:
    def __init__(self):
        self.settings = get_settings()
        self.memory: list[Chunk] = []
        self.documents = {}
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=140)
        if self.settings.demo_mode:
            for name, text in DEMO_DOCS.items():
                self.add(name, [(None, text)], "general")
        else:
            self.embeddings = OpenAIEmbeddings(model=self.settings.openai_embedding_model, api_key=self.settings.openai_api_key)
            pc = Pinecone(api_key=self.settings.pinecone_api_key)
            if not pc.has_index(self.settings.pinecone_index):
                pc.create_index(name=self.settings.pinecone_index, dimension=1536, metric="cosine", spec=ServerlessSpec(cloud=self.settings.pinecone_cloud, region=self.settings.pinecone_region))
            self.index = pc.Index(self.settings.pinecone_index)

    def add(self, filename, pages, category="general"):
        doc_id = str(uuid.uuid4())
        chunks = []
        for page, text in pages:
            for part in self.splitter.split_text(text):
                if part.strip():
                    chunks.append(Chunk(str(uuid.uuid4()), part, {"document_id": doc_id, "filename": filename, "page": page, "category": category}))
        if self.settings.demo_mode:
            self.memory.extend(chunks)
        else:
            vectors = self.embeddings.embed_documents([c.text for c in chunks])
            self.index.upsert([(c.id, vector, {**c.metadata, "text": c.text}) for c, vector in zip(chunks, vectors)])
        self.documents[doc_id] = {"id": doc_id, "filename": filename, "chunks": len(chunks), "category": category}
        return self.documents[doc_id]

    def search(self, query, category, document_ids, limit=5):
        if self.settings.demo_mode:
            terms = set(re.findall(r"\w+", query.lower()))
            allowed = [c for c in self.memory if not document_ids or c.metadata["document_id"] in document_ids]
            for c in allowed:
                words = set(re.findall(r"\w+", c.text.lower()))
                c.score = len(terms & words) / max(len(terms), 1)
            return sorted(allowed, key=lambda c: c.score, reverse=True)[:limit]
        vector = self.embeddings.embed_query(query)
        filt = {"document_id": {"$in": document_ids}} if document_ids else None
        result = self.index.query(vector=vector, top_k=limit, include_metadata=True, filter=filt)
        return [Chunk(m.id, m.metadata["text"], m.metadata, m.score) for m in result.matches]

    def delete(self, doc_id):
        if self.settings.demo_mode:
            self.memory = [c for c in self.memory if c.metadata["document_id"] != doc_id]
        else:
            self.index.delete(filter={"document_id": doc_id})
        return self.documents.pop(doc_id, None) is not None

