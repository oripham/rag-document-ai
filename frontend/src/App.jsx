import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Send, FileUp, Bot, Cpu, Database, Trash2, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const App = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [apiUrl, setApiUrl] = useState(""); // Để trống để nhập URL Cloudflare
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0); // Tiến độ tải lên
  const [chunks, setChunks] = useState([]);
  const [files, setFiles] = useState([]); // Danh sách tên file
  const chatEndRef = useRef(null);

  const fetchFiles = async (url) => {
    try {
      const cleanUrl = url.replace(/\/$/, "");
      const res = await axios.get(`${cleanUrl}/files`);
      setFiles(res.data.files || []);
    } catch (e) { console.error("Lỗi lấy danh sách file", e); }
  };

  useEffect(() => {
    fetchFiles(apiUrl);
  }, [apiUrl]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleUpload = async (file) => {
    if (!file) return;
    const cleanUrl = apiUrl.replace(/\/$/, "");
    const formData = new FormData();
    formData.append("file", file);
    try {
      setIsLoading(true);
      setUploadProgress(1); // Bắt đầu chạy thanh tiến độ
      
      const res = await axios.post(`${cleanUrl}/upload`, formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      setChunks(new Array(res.data.total_chunks).fill(0));
      await fetchFiles(apiUrl);
    } catch (error) {
      console.error(error);
      alert("Lỗi tải/embedding tài liệu!");
    } finally {
      setIsLoading(false);
      setTimeout(() => setUploadProgress(0), 1000); // Reset sau 1s
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  };

  const handleDeleteFile = async (filename) => {
    if (!window.confirm(`Xóa file ${filename}?`)) return;
    const cleanUrl = apiUrl.replace(/\/$/, "");
    try {
      setIsLoading(true);
      await axios.post(`${cleanUrl}/delete_file`, { filename });
      fetchFiles(apiUrl);
    } catch (e) { alert("Lỗi khi xóa file!"); }
    finally { setIsLoading(false); }
  };

  const handleClear = async () => {
    if (!window.confirm("Xóa toàn bộ dữ liệu?")) return;
    const cleanUrl = apiUrl.replace(/\/$/, "");
    try {
      await axios.post(`${cleanUrl}/clear`);
      setChunks([]);
      setMessages([]);
      await fetchFiles(apiUrl); // Đồng bộ lại danh sách file thực tế từ Server
      alert("Đã xóa sạch dữ liệu!");
    } catch (error) {
      alert("Lỗi khi xóa dữ liệu!");
    }
  };

    const handleSend = async () => {
    if (!input.trim() || !apiUrl || isLoading) return;

    const cleanUrl = apiUrl.replace(/\/$/, "");
    const currentInput = input; // Lưu lại câu hỏi trước khi xóa ô nhập
    const userMessage = { role: "user", text: currentInput };
    
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const botPlaceholder = { role: "bot", text: "", sources: [] };
    setMessages((prev) => [...prev, botPlaceholder]);

    try {
      const response = await fetch(`${cleanUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentInput }), // Dùng currentInput ở đây
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(errorData || "Can't connect to API");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulatedText += decoder.decode(value, { stream: true });

        setMessages((prev) => {
          const newMsg = [...prev];
          newMsg[newMsg.length - 1] = { ...newMsg[newMsg.length - 1], text: accumulatedText };
          return newMsg;
        });
      }
    } catch (e) {
      console.error("Lỗi Chat Detail:", e);
      setMessages((prev) => {
        const newMsg = [...prev];
        newMsg[newMsg.length - 1] = { ...newMsg[newMsg.length - 1], text: `Lỗi kết nối Backend: ${e.message}` };
        return newMsg;
      });
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="flex h-screen w-full bg-[#f0f9ff] text-black antialiased overflow-hidden font-['Inter']">
      {/* Sidebar - Cấu hình */}
      <motion.aside
        initial={{ x: -280 }}
        animate={{ x: 0 }}
        className="w-72 bg-white border-r border-[#bae6fd] p-6 flex flex-col z-20"
      >
        <div className="flex items-center gap-2 mb-8">
          <Bot className="text-blue-600" size={28} />
          <h2 className="text-lg font-bold text-slate-800">Cấu hình</h2>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto">
          <div>
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Dán URL Cloudflare</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full bg-[#f8fafc] border border-blue-200 rounded-lg px-4 py-3 text-sm focus:border-blue-500 outline-none font-bold text-blue-700"
              placeholder="https://...trycloudflare.com"
            />
          </div>

          <div>
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-2">Tài liệu (PDF/Docx/Ảnh)</label>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:bg-slate-50 transition-all cursor-pointer"
              onClick={() => document.getElementById("file-upload").click()}
            >
              <FileUp className="mx-auto mb-2 text-slate-300" size={24} />
              <p className="text-[11px] text-slate-500 font-bold uppercase tracking-tighter">Chọn hoặc thả file</p>
              <input id="file-upload" type="file" onChange={(e) => handleUpload(e.target.files[0])} className="hidden" accept=".pdf,.docx,.png,.jpg,.jpeg" />
            </div>

            {/* Thanh tiến độ tải lên */}
            <AnimatePresence>
              {uploadProgress > 0 && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4"
                >
                  <div className="flex justify-between text-[10px] font-bold text-blue-500 mb-1 uppercase tracking-widest">
                    <span>Đang tải lên...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-blue-50 h-2 rounded-full overflow-hidden border border-blue-100">
                    <motion.div 
                      className="bg-blue-500 h-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Danh sách file đã tải lên */}
            <div className="mt-4 space-y-2">
              {files.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between bg-[#f0f9ff] p-2 px-3 rounded-lg border border-blue-100 group">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <div className="min-w-[6px] h-1.5 bg-blue-400 rounded-full" />
                    <span className="text-xs font-bold text-slate-700 truncate">{file}</span>
                  </div>
                  <button 
                    onClick={() => handleDeleteFile(file)}
                    className="text-red-400 hover:text-red-600 p-1 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {files.length === 0 && (
                <p className="text-[10px] text-slate-400 italic text-center">Chưa có tài liệu.</p>
              )}
            </div>
          </div>

          <div>
             <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-1.5">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Bộ nhớ</label>
                  <button 
                    onClick={() => fetchFiles(apiUrl)} 
                    className="p-1 hover:text-blue-500 transition-all text-slate-300"
                    title="Làm mới danh sách"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
                  </button>
                </div>
                <button onClick={handleClear} className="p-1 hover:text-red-500 transition-all"><Trash2 size={16} /></button>
             </div>
             <div className="bg-[#f8fafc] border border-slate-100 rounded-xl p-3">
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span>Trạng thái:</span>
                  <span className="text-blue-600">{chunks.length > 0 ? "Sẵn sàng" : "Trống"}</span>
                </div>
                {chunks.length > 0 && (
                   <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2">
                      <div className="bg-blue-500 h-full w-full rounded-full" />
                   </div>
                )}
             </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-blue-100 text-[10px] text-center text-blue-400 font-bold uppercase tracking-widest">
           Cloudflare GPU Mode Active
        </div>
      </motion.aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col bg-[#e0f2fe]">
        <header className="h-14 flex items-center px-8 border-b border-[#bae6fd] bg-white/50">
           <span className="text-lg font-bold text-slate-700 tracking-tight">HỆ THỐNG CHATBOT</span>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-10 space-y-6">
          <AnimatePresence>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`max-w-[85%] p-5 rounded-2xl shadow-sm ${
                  msg.role === "user" 
                    ? "bg-[#3b82f6] text-white rounded-tr-none text-xl font-medium" 
                    : "bg-white text-black rounded-tl-none border-2 border-[#3b82f6] text-xl font-bold"
                }`}>
                  <p className="leading-snug whitespace-pre-wrap">{msg.text}</p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="px-10 pb-8">
          <div className="max-w-4xl mx-auto bg-white border-2 border-[#3b82f6] rounded-2xl p-2 flex items-center gap-2 shadow-xl">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              className="flex-1 bg-transparent px-6 py-3 text-black font-bold text-xl outline-none"
              placeholder="Nhập câu hỏi của bạn..."
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="w-14 h-14 bg-[#3b82f6] text-white rounded-xl flex items-center justify-center hover:bg-blue-600 transition-all font-bold"
            >
              <Send size={24} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
