import uuid
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from .config import get_settings
from .services import VectorStore, Chunk

class GraphState(TypedDict):
    question: str
    history: list
    document_ids: list[str]
    route: str
    chunks: list[Chunk]
    answer: str

class RagGraph:
    def __init__(self, store: VectorStore):
        self.store = store
        self.settings = get_settings()
        self.llm = None if self.settings.demo_mode else ChatOpenAI(model=self.settings.openai_chat_model, temperature=0, api_key=self.settings.openai_api_key)
        graph = StateGraph(GraphState)
        graph.add_node("coordinator", self.coordinator)
        for name in ("technical", "financial", "general"):
            graph.add_node(name, self.retrieve)
        graph.add_node("answer", self.answer)
        graph.set_entry_point("coordinator")
        graph.add_conditional_edges("coordinator", lambda s: s["route"], {x: x for x in ("technical", "financial", "general")})
        for name in ("technical", "financial", "general"):
            graph.add_edge(name, "answer")
        graph.add_edge("answer", END)
        self.app = graph.compile()

    def coordinator(self, state):
        q = state["question"].lower()
        finance = {"revenue", "cost", "profit", "invoice", "budget", "financial", "price"}
        tech = {"api", "code", "architecture", "deploy", "database", "python", "aws", "error", "security"}
        route = "financial" if any(x in q for x in finance) else "technical" if any(x in q for x in tech) else "general"
        return {"route": route}

    def retrieve(self, state):
        return {"chunks": self.store.search(state["question"], state["route"], state["document_ids"])}

    def answer(self, state):
        if not state["chunks"]:
            return {"answer": "I couldn't find relevant information in the selected documents."}
        if self.settings.demo_mode:
            text = " ".join(c.text for c in state["chunks"][:2])
            return {"answer": f"Based on the indexed documents, {text[:650]} [1]"}
        context = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(state["chunks"], 1))
        history = "\n".join(f'{m["role"]}: {m["content"]}' for m in state["history"][-6:])
        prompt = f"You are the {state['route']} document specialist. Answer only from context. Cite claims using [1], [2]. If evidence is missing, say so.\nHistory:\n{history}\nContext:\n{context}\nQuestion: {state['question']}"
        return {"answer": self.llm.invoke(prompt).content}

    def invoke(self, question, history, document_ids):
        return self.app.invoke({"question": question, "history": history, "document_ids": document_ids, "route": "general", "chunks": [], "answer": ""})

