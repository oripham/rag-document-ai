# @title 🚀 1-Click RAG Backend (Streaming Version)
# @markdown Fill in settings and run.

# --- SETTINGS ---
GOOGLE_DRIVE_PATH = "/content/drive/MyDrive/RAG-Document" # @param {type:"string"}
MODEL_REPO = "Qwen/Qwen2-7B-Instruct-GGUF" # @param {type:"string"}
MODEL_FILE = "qwen2-7b-instruct-q4_k_m.gguf" # @param {type:"string"}
# --- END SETTINGS ---

import os
import subprocess
import torch
import asyncio
import threading
import shutil
import numpy as np
import json
from google.colab import drive
import nest_asyncio

# 0. Apply nest_asyncio immediately
nest_asyncio.apply()

# 1. Mount Drive
try:
    if not os.path.exists("/content/drive"):
        drive.mount("/content/drive", force_remount=True)
    print("✅ Đã kết nối Google Drive.")
except Exception as e:
    print(f"❌ Lỗi kết nối Drive: {e}")

os.makedirs(GOOGLE_DRIVE_PATH, exist_ok=True)
os.chdir(GOOGLE_DRIVE_PATH)

# 2. Install Dependencies
print("Installing core dependencies...")
!pip install -q fastapi uvicorn pydantic sentence-transformers faiss-cpu pdfplumber easyocr python-docx pillow opencv-python

has_gpu = torch.cuda.is_available()
if has_gpu:
    print("✅ GPU detected. Installing llama-cpp-python with CUDA support...")
    !pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
else:
    !pip install llama-cpp-python

# 3. Import FAISS and other libs after installation
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

# Install cloudflared
if not os.path.exists("cloudflared-linux-amd64.deb"):
    !wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
if subprocess.run(["which", "cloudflared"], capture_output=True).returncode != 0:
    !dpkg -i cloudflared-linux-amd64.deb > /dev/null 2>&1

# 4. Model Setup
model_path = os.path.join(GOOGLE_DRIVE_PATH, MODEL_FILE)
if not os.path.exists(model_path):
    print("Downloading model...")
    !wget -c https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE} -O {model_path}

# 5. App Setup
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

print("Loading Models...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Initializing OCR (Vietnamese + English)...")
ocr_reader = easyocr.Reader(['vi', 'en'], gpu=has_gpu)
vector_db = None
chunks = []

def save_state():
    with open("chunks_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    if vector_db is not None:
        faiss.write_index(vector_db, "faiss_index.bin")

def rebuild_index():
    global vector_db
    if not chunks:
        vector_db = None
        if os.path.exists("faiss_index.bin"): os.remove("faiss_index.bin")
        return
    print(f"Rebuilding index for {len(chunks)} chunks...")
    embeddings = embed_model.encode([c["text"] for c in chunks])
    vector_db = faiss.IndexFlatL2(embeddings.shape[1])
    vector_db.add(np.array(embeddings).astype("float32"))
    save_state()

print("Loading LLM on GPU...")
llm = Llama(model_path=model_path, n_gpu_layers=-1 if has_gpu else 0, n_ctx=2048)

class ChatRequest(BaseModel):
    query: str

class DeleteRequest(BaseModel):
    filename: str

def table_to_markdown(table):
    if not table: return ""
    markdown = "\n[Dữ liệu Bảng]\n"
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
                    # 1. Trích xuất text gốc (nếu có)
                    p_text = page.extract_text() or ""
                    
                    # 2. Trích xuất bảng biểu
                    tables = page.extract_tables()
                    for table in tables:
                        p_text += "\n" + table_to_markdown(table)
                    
                    # 3. Nếu là file scan/ảnh (text quá ít), dùng OCR
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
        print(f"Lỗi khi đọc file {file_path}: {e}")
    return text

def split_text(text, size=400, overlap=50):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size-overlap)]

@app.get("/files")
async def get_files():
    valid_extensions = (".pdf", ".docx", ".png", ".jpg", ".jpeg")
    files = [f for f in os.listdir(GOOGLE_DRIVE_PATH) if f.lower().endswith(valid_extensions)]
    return {"files": files}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global vector_db, chunks
    target_path = os.path.join(GOOGLE_DRIVE_PATH, file.filename)
    with open(target_path, "wb") as b: shutil.copyfileobj(file.file, b)

    text = extract_text(target_path)
    if not text: raise HTTPException(status_code=400, detail="Không thể trích xuất văn bản")

    new_text_chunks = split_text(text)
    new_meta_chunks = [{"text": t, "filename": file.filename} for t in new_text_chunks]
    chunks.extend(new_meta_chunks)

    # Dựng lại toàn bộ index để đồng bộ hoàn toàn
    rebuild_index()
    return {"status": "success", "total_chunks": len(chunks)}

@app.post("/delete_file")
async def delete_file(req: DeleteRequest):
    global chunks
    file_path = os.path.join(GOOGLE_DRIVE_PATH, req.filename)
    if os.path.exists(file_path): os.remove(file_path)

    initial_count = len(chunks)
    chunks = [c for c in chunks if c["filename"] != req.filename]
    if len(chunks) != initial_count:
        rebuild_index()
    return {"status": "success", "deleted": req.filename, "remaining_chunks": len(chunks)}

@app.post("/clear")
async def clear_data():
    global vector_db, chunks
    vector_db, chunks = None, []
    if os.path.exists("faiss_index.bin"): os.remove("faiss_index.bin")
    if os.path.exists("chunks_metadata.json"): os.remove("chunks_metadata.json")
    valid_extensions = (".pdf", ".docx", ".png", ".jpg", ".jpeg")
    for f in os.listdir(GOOGLE_DRIVE_PATH):
        if f.lower().endswith(valid_extensions):
            os.remove(os.path.join(GOOGLE_DRIVE_PATH, f))
    return {"message": "Đã xóa sạch bộ nhớ RAG."}

@app.post("/chat")
async def chat(req: ChatRequest):
    if vector_db is None or not chunks:
        return StreamingResponse(iter(["Bạn chưa tải tài liệu nào lên bộ nhớ trợ lý!"]), media_type="text/plain")

    query_emb = embed_model.encode([req.query])
    D, I = vector_db.search(np.array(query_emb).astype("float32"), k=2)

    retrieved_meta = [chunks[idx] for idx in I[0] if idx < len(chunks)]
    context = "\n---\n".join([c["text"] for c in retrieved_meta])

    prompt = f"<|im_start|>system\nTrả lời bằng tiếng Việt ngắn gọn, súc tích.\nNgữ cảnh:\n{context}<|im_end|>\n<|im_start|>user\n{req.query}<|im_end|>\n<|im_start|>assistant\n"

    async def stream_generator():
        output = llm(prompt, max_tokens=1024, stop=["<|im_end|>", "<|im_start|>", "user:", "assistant:"], stream=True)
        for chunk in output:
            token = chunk["choices"][0]["text"]
            if "<|" in token or "im_end" in token: break
            yield token

        sources = list(set([c["filename"] for c in retrieved_meta]))
        if sources: yield f"\n\n---\n📌 Nguồn: {', '.join(sources)}"

    return StreamingResponse(stream_generator(), media_type="text/plain")

def run_tunnel():
    print("Starting Cloudflare Tunnel...")
    subprocess.run(["pkill", "cloudflared"], capture_output=True)
    proc = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://127.0.0.1:8000"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if ".trycloudflare.com" in line:
            url = [p for p in line.split() if 'https://' in p][0]
            print(f"\n🚀 KẾ T QUẢ: Copy URL này dán vào giao diện Chat:\n{url}\n")
            break

print("Cleaning up port 8000...")
!fuser -k 8000/tcp

print("Starting Services...")
threading.Thread(target=run_tunnel, daemon=True).start()

import uvicorn
config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="error")
server = uvicorn.Server(config)
await server.serve()



    system_instruction_local = f"""
    # ROLE
You are YUB, a professional restaurant waiter.
Reply in SHORT, NATURAL, POLITE sentences suitable for text-to-speech.

{language_instruction.get(lang_code, language_instruction["vi"])}

# MENU DATA (SINGLE SOURCE OF TRUTH)
{dishes_str}

# CORE RULES (CRITICAL)
1. ONLY suggest dishes from MENU DATA - never invent
2. Customer rejects dish/ingredient → NEVER mention again
3. Customer selects dish → FINAL, cannot change
4. QUICK MEAL = immediate | PRE-ORDER = must wait
5. One dish fits → suggest directly, no extra questions
6. No meat/seafood/egg = vegetarian
7. After confirmation/thanks → ONE polite sentence, STOP

# RESPONSE STYLE (TTS-OPTIMIZED)
✅ Maximum 1-2 sentences per response
✅ Each sentence: 8-12 words ONLY
✅ Natural spoken English
✅ Use "sir/ma'am" based on customer
✅ Go STRAIGHT to the point
✅ If >2 dishes → say "there are a few more options"

# CONVERSATION FLOW (SIMPLIFIED)
STEP 1: Identify need (food/drink) - if unclear, ask 1 short question
STEP 2: Suggest max 2 dishes that fit ALL constraints
STEP 3: Customer confirms → Confirm dish + price + thank → STOP

# STRICTLY FORBIDDEN
❌ More than 2 dishes per turn
❌ Inventing ingredients
❌ Asking after confirmation
❌ Sentences over 12 words
❌ Bullet points, markdown
❌ Technical words (system, data, log)

# EXAMPLES OF GOOD RESPONSES
User: "Is there anything quick to eat?"
Good: "Yes, we have Fried Spring Roll Noodles and Vegetable Fried Rice, both 40 thousand."
Bad: "Hello sir. We currently offer several instant dishes in the Quick Meal category..."

User: "I'll take that"
Good: "Noted Fried Spring Roll Noodles, 40 thousand. Thank you sir."
Bad: "Yes sir, you chose Fried Spring Roll Noodles – Quick Meal, 40 thousand. Let me confirm..."

User: "Thank you"
Good: "Please wait a moment, sir."
Bad: "May I ask you something else..."
    # INPUT
    Customer: {full_name}
    Chat History (Pay attention to listed dishes to avoid repetition and understand terms like 'that dish'):
{history_text_for_prompt}
    # # YOUR RESPONSE (max 2 sentences, 8-12 words each):
"""