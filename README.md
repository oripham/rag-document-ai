# 🤖 Local RAG Chatbot (OCR + LLM)

Hệ thống Chatbot dựa trên kiến trúc **RAG (Retrieval-Augmented Generation)** tích hợp công nghệ **OCR** để xử lý đa dạng các loại tài liệu (PDF, Word, Ảnh). Dự án này được tối ưu hóa để chạy hoàn toàn cục bộ trên máy tính cá nhân.

## 📁 Cấu trúc thư mục
```
├── README.md               # Hướng dẫn sử dụng
├── .gitignore              # Các file bỏ qua trong Git
├── backend/                # Mã nguồn Python (FastAPI)
│   ├── main.py             # Script chạy backend
│   ├── requirements.txt    # Danh sách thư viện cần thiết
│   ├── references/         # (Tham khảo) Notebook phát triển ban đầu
│   ├── models/             # Chứa file mô hình .gguf (tự tạo)
│   └── uploads/            # Thư mục chứa tài liệu tải lên
├── frontend/               # Giao diện người dùng (React/Vite)
└── docs/                   # Tài liệu test hệ thống(PDF)
```

## 🛠️ Yêu cầu hệ thống
- Python 3.9+
- Node.js & npm
- C++ Build Tools (để cài đặt `llama-cpp-python`) hoặc card đồ họa NVIDIA (nếu chạy GPU).

## 🚀 Hướng dẫn cài đặt

### 1. Chuẩn bị Backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

**Lưu ý về Mô hình (Model):**
Bạn cần tải phiên bản GGUF của mô hình LLM (ví dụ: `qwen2-7b-instruct-q4_k_m.gguf`) từ HuggingFace và đặt vào thư mục `backend/models/`.

### 2. Chuẩn bị Frontend
```bash
cd frontend
npm install
```

## 🏃 Cách chạy ứng dụng

### 1. Khởi động Backend (Local)
```bash
cd backend
python main.py
```
Server sẽ chạy tại `http://localhost:8000`.

### 2. Khởi động Frontend
```bash
cd frontend
npm run dev
```
Truy cập giao diện tại `http://localhost:5173`.

### 3. Kết nối Giao diện với Backend
> [!IMPORTANT]
> - Sau khi Frontend khởi động, bạn cần nhập URL của Backend vào ô cấu hình trong giao diện.
> - Nếu chạy **Local**: Dùng `http://localhost:8000` hoặc `http://127.0.0.1:8000`.
> - Nếu chạy **Colab**: Dùng link `https://xxxx.trycloudflare.com` do `cloudflared` cung cấp.

---

## ☁️ Chạy trên Google Colab (Tùy chọn)
Nếu máy tính cá nhân không đủ cấu hình (thiếu GPU hoặc RAM ít), bạn có thể sử dụng bản Notebook đi kèm trong thư mục `backend/references/`.

1. Tải thư mục này lên Google Drive của bạn.
2. Mở tệp `backend.ipynb` bằng Google Colab.
3. Chỉnh sửa tham số `GOOGLE_DRIVE_PATH` trỏ đúng vào thư mục dự án trên Drive của bạn.
4. Chạy tất cả các ô (Run all). Hệ thống sẽ tự động cung cấp một link **Cloudflare Tunnel** để bạn dán vào giao diện Chat.

---
## ✨ Tính năng chính
- **OCR:** Tự động trích xuất chữ từ ảnh và PDF quét.
- **Table Extraction:** Nhận diện và chuyển đổi bảng biểu sang định dạng Markdown để LLM hiểu tốt hơn.
- **RAG:** Truy hồi ngữ cảnh chính xác bằng FAISS và MiniLM.
- **Streaming:** Phản hồi của chatbot được hiển thị theo dạng phát trực tiếp (streaming) mượt mà.

---

