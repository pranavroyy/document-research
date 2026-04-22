from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.chat import router as chat_router

# Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Research Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "AI Research Assistant API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}