# 🤖 Local RAG Chatbot (OCR + LLM)

A professional **Retrieval-Augmented Generation (RAG)** chatbot system integrated with **OCR** technology for processing diverse document formats (PDF, Word, Images). Optimized for low-latency local execution.

---

## 📁 Project Structure
```text
├── README.md               # User guide (English)
├── .gitignore              # Git ignore rules
├── backend/                # FastAPI source code
│   ├── main.py             # Main entry point for local execution
│   ├── requirements.txt    # Python dependencies
│   ├── references/         # (Reference) Original Colab Notebook
│   ├── models/             # Local GGUF models storage
│   └── uploads/            # Local document storage
├── frontend/               # User Interface (React + Vite)
└── docs/                   # System test documents (PDF)
```

## 🛠️ System Requirements
- Python 3.9+
- Node.js & npm
- C++ Build Tools (for `llama-cpp-python`) or NVIDIA GPU (with CUDA support).

## 🚀 Getting Started

### 1. Backend Setup
1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate

   pip install -r requirements.txt
   ```
2. **Download Model:** Place your preferred GGUF model (e.g., `qwen2-7b-instruct-q4_k_m.gguf`) into the `backend/models/` directory.

### 2. Frontend Setup
1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```

### 3. Connection Configuration
> [!IMPORTANT]
> - After the frontend starts, you must enter the Backend URL in the configuration field within the chat interface.
> - **Local Setup:** Use `http://localhost:8000` or `http://127.0.0.1:8000`.
> - **Colab Setup:** Use the `https://xxxx.trycloudflare.com` link provided by the `cloudflared` tunnel.

---

## ☁️ Google Colab Deployment (Alternative)
If your local hardware is limited (lack of GPU or low RAM), you can use the original notebook provided in the `backend/references/` directory.

1. Upload this directory to your Google Drive.
2. Open `backend.ipynb` with Google Colab.
3. Edit the `GOOGLE_DRIVE_PATH` parameter to match your project folder.
4. "Run all" cells. The system will automatically generate a **Cloudflare Tunnel** link for the frontend connection.

---

## ✨ Key Features
- **Smart OCR:** Automated text extraction from images and scanned PDFs using **EasyOCR**.
- **Table Extraction:** Advanced table-to-markdown conversion for improved LLM context understanding.
- **Efficient Retrieval:** Semantic search powered by **FAISS** and **MiniLM-L6-v2**.
- **Streaming Response:** Real-time token generation for a smooth user experience.

---
