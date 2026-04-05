import os
import shutil
import numpy as np
import json
import faiss
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import pdfplumber
import easyocr
from docx import Document
from PIL import Image

# --- CONFIGURATION ---
UPLOAD_DIR = "./uploads"
MODEL_PATH = "./models/qwen2-7b-instruct-q4_k_m.gguf"
METADATA_FILE = "chunks_metadata.json"
FAISS_INDEX_FILE = "faiss_index.bin"
TOP_K = 2
MAX_TOKENS = 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

# --- APP SETUP ---
app = FastAPI(title="Local RAG Chatbot Backend")

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE ---
print("Loading Embedding Model (Sentence-Transformers)...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Initializing OCR (Vietnamese + English)...")
# Check if GPU is available for OCR
import torch
use_gpu = torch.cuda.is_available()
ocr_reader = easyocr.Reader(['vi', 'en'], gpu=use_gpu)

vector_db = None
chunks = []

# --- LLM SETUP ---
llm = None
if os.path.exists(MODEL_PATH):
    print(f"Loading LLM from {MODEL_PATH}...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=-1 if use_gpu else 0,
        n_ctx=2048,
        verbose=False
    )
else:
    print(f"⚠️ Warning: Model not found at {MODEL_PATH}. Chat feature will be disabled until model is downloaded.")

# --- UTILITIES ---
def save_state():
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    if vector_db is not None:
        faiss.write_index(vector_db, FAISS_INDEX_FILE)

def load_state():
    global chunks, vector_db
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    if os.path.exists(FAISS_INDEX_FILE):
        vector_db = faiss.read_index(FAISS_INDEX_FILE)

def rebuild_index():
    global vector_db
    if not chunks:
        vector_db = None
        if os.path.exists(FAISS_INDEX_FILE): os.remove(FAISS_INDEX_FILE)
        return
    
    print(f"Indexing {len(chunks)} chunks...")
    embeddings = embed_model.encode([c["text"] for c in chunks])
    vector_db = faiss.IndexFlatL2(embeddings.shape[1])
    vector_db.add(np.array(embeddings).astype("float32"))
    save_state()

def table_to_markdown(table):
    if not table: return ""
    markdown = "\n[Table Data]\n"
    for row in table:
        markdown += "| " + " | ".join([str(cell).strip().replace("\n", " ") if cell else "" for cell in row]) + " |\n"
    return markdown

def extract_text(file_path):
    text = ""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    p_text = page.extract_text() or ""
                    tables = page.extract_tables()
                    for table in tables:
                        p_text += "\n" + table_to_markdown(table)
                    
                    if len(p_text.strip()) < 50:
                        img = page.to_image().original.convert("RGB")
                        ocr_res = ocr_reader.readtext(np.array(img), detail=0)
                        p_text += " " + " ".join(ocr_res)
                    text += p_text + "\n"
        elif ext == ".docx":
            text = " ".join([p.text for p in Document(file_path).paragraphs])
        elif ext in [".png", ".jpg", ".jpeg"]:
            ocr_res = ocr_reader.readtext(file_path, detail=0)
            text = " ".join(ocr_res)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return text

def split_text(text, size=400, overlap=50):
    words = text.split()
    if not words: return []
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size - overlap)]

# Load existing data on startup
load_state()

# --- MODELS ---
class ChatRequest(BaseModel):
    query: str

class DeleteRequest(BaseModel):
    filename: str

# --- ENDPOINTS ---
@app.get("/files")
async def get_files():
    valid_extensions = (".pdf", ".docx", ".png", ".jpg", ".jpeg")
    files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(valid_extensions)]
    return {"files": files}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global chunks
    target_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(target_path, "wb") as b:
        shutil.copyfileobj(file.file, b)

    text = extract_text(target_path)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file.")

    new_text_chunks = split_text(text)
    new_meta_chunks = [{"text": t, "filename": file.filename} for t in new_text_chunks]
    chunks.extend(new_meta_chunks)

    rebuild_index()
    return {"status": "success", "total_chunks": len(chunks)}

@app.post("/delete_file")
async def delete_file(req: DeleteRequest):
    global chunks
    file_path = os.path.join(UPLOAD_DIR, req.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    initial_count = len(chunks)
    chunks = [c for c in chunks if c["filename"] != req.filename]
    if len(chunks) != initial_count:
        rebuild_index()
    return {"status": "success", "deleted": req.filename, "remaining_chunks": len(chunks)}

@app.post("/clear")
async def clear_data():
    global vector_db, chunks
    vector_db, chunks = None, []
    if os.path.exists(FAISS_INDEX_FILE): os.remove(FAISS_INDEX_FILE)
    if os.path.exists(METADATA_FILE): os.remove(METADATA_FILE)
    
    valid_extensions = (".pdf", ".docx", ".png", ".jpg", ".jpeg")
    for f in os.listdir(UPLOAD_DIR):
        if f.lower().endswith(valid_extensions):
            os.remove(os.path.join(UPLOAD_DIR, f))
    return {"message": "RAG storage cleared."}

@app.post("/chat")
async def chat(req: ChatRequest):
    if llm is None:
        return StreamingResponse(iter(["Error: Model not loaded. Check backend logs."]), media_type="text/plain")
    
    if vector_db is None or not chunks:
        return StreamingResponse(iter(["You haven't uploaded any documents yet!"]), media_type="text/plain")

    # Search
    query_emb = embed_model.encode([req.query])
    D, I = vector_db.search(np.array(query_emb).astype("float32"), k=TOP_K)

    retrieved_meta = [chunks[idx] for idx in I[0] if idx < len(chunks)]
    context = "\n---\n".join([c["text"] for c in retrieved_meta])

    prompt = f"<|im_start|>system\nTrả lời bằng tiếng Việt ngắn gọn, súc tích.\nNgữ cảnh:\n{context}<|im_end|>\n<|im_start|>user\n{req.query}<|im_end|>\n<|im_start|>assistant\n"

    async def stream_generator():
        output = llm(prompt, max_tokens=MAX_TOKENS, stop=["<|im_end|>", "<|im_start|>"], stream=True)
        for chunk in output:
            token = chunk["choices"][0]["text"]
            if "<|" in token or "im_end" in token: break
            yield token

        sources = list(set([c["filename"] for c in retrieved_meta]))
        if sources:
            yield f"\n\n---\n📌 Nguồn: {', '.join(sources)}"

    return StreamingResponse(stream_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
