# 🤖 Local RAG Chatbot — OCR + LLM

> A personal project building a **Retrieval-Augmented Generation (RAG)** system integrated with **OCR**, enabling intelligent conversations based on document content (PDF, Word, Images) — running entirely on a local machine.

---

## 🎯 Purpose

Build a personal chatbot capable of:

- **Reading and understanding documents** in multiple formats: PDF (including scanned), Word (.docx), and images (.png, .jpg).
- **Automatically extracting information** using OCR (Optical Character Recognition) for scanned documents or photos.
- **Answering questions** based on uploaded document content, using RAG technique — semantic search combined with a Large Language Model (LLM).
- **Running offline**, with no dependency on external APIs, ensuring data privacy.

---

## 🛠️ Tech Stack

### Backend

| Technology | Role |
|---|---|
| **Python** | Primary language |
| **FastAPI** | Web framework for REST API |
| **Uvicorn** | ASGI server |
| **llama-cpp-python** | Run LLM models in GGUF format on CPU/GPU |
| **Qwen2-7B (GGUF)** | Large Language Model with Vietnamese support |

### AI & Machine Learning

| Technology | Role |
|---|---|
| **FAISS** | Vector database — high-speed semantic search |
| **Sentence-Transformers** (MiniLM-L6-v2) | Text-to-vector embedding |
| **EasyOCR** | Optical Character Recognition (Vietnamese + English) |
| **PyTorch** | Backend for AI models |
| **pdfplumber** | Extract text & tables from PDF |
| **python-docx** | Read Word (.docx) files |
| **Pillow / OpenCV** | Image processing |

### Frontend

| Technology | Role |
|---|---|
| **React 19** | UI library |
| **Vite** | Build tool & dev server |
| **TailwindCSS 4** | Styling |
| **Framer Motion** | Animations |
| **Axios** | HTTP client for backend communication |
| **Lucide React** | Icon library |

---

## 📁 Project Structure

```text
├── README.md               # User guide
├── .gitignore              # Git ignore rules
├── backend/                # FastAPI backend
│   ├── main.py             # Main entry point
│   ├── requirements.txt    # Python dependencies
│   ├── references/         # Original notebook (Google Colab)
│   ├── models/             # GGUF model storage
│   └── uploads/            # Document storage
├── frontend/               # User Interface (React + Vite)
└── docs/                   # System test documents (PDF)
```

---

## 🚀 Getting Started

### System Requirements
- Python 3.9+
- Node.js & npm
- C++ Build Tools (for `llama-cpp-python`) or NVIDIA GPU (with CUDA support)

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

> [!IMPORTANT]
> **Download Model:** Place your GGUF model file (e.g., `qwen2-7b-instruct-q4_k_m.gguf`) into the `backend/models/` directory.

Start the server:
```bash
python main.py
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Connection Configuration

> [!IMPORTANT]
> - After the frontend starts, enter the **Backend URL** in the configuration field within the chat interface.
> - **Local:** Use `http://localhost:8000` or `http://127.0.0.1:8000`.
> - **Colab:** Use the `https://xxxx.trycloudflare.com` link from Cloudflare Tunnel.

---

## ☁️ Google Colab Deployment (Alternative)

If your local hardware is limited (no GPU or low RAM), you can use the notebook in the `backend/references/` directory:

1. Upload the project directory to Google Drive.
2. Open `backend.ipynb` with Google Colab.
3. Edit the `GOOGLE_DRIVE_PATH` parameter to match your project folder.
4. Run all cells — the system will automatically generate a **Cloudflare Tunnel** link for frontend connection.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📄 **Smart OCR** | Automatic text extraction from images and scanned PDFs using EasyOCR |
| 📊 **Table Extraction** | PDF table-to-Markdown conversion for better LLM comprehension |
| 🔍 **Semantic Search** | Vector-based retrieval powered by FAISS + MiniLM-L6-v2 |
| ⚡ **Streaming Response** | Real-time token-by-token generation |
| 📁 **File Management** | Upload, delete, and browse uploaded documents |
| 🔒 **Fully Offline** | All processing runs locally, ensuring data privacy |
