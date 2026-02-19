import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, FileSpreadsheet, Paperclip, Sparkles, Bot, User } from "lucide-react";
import type { UploadedFile } from "./FileUploadPanel";

export interface ChatMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
  table?: { headers: string[]; rows: any[][] };
}

interface ChatAreaProps {
  messages: ChatMessage[];
  currentFile: UploadedFile | null;
  onSendMessage: (message: string) => void;
  onUploadClick: () => void;
  isTyping: boolean;
}

const TypingIndicator = () => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0 }}
    className="flex items-start gap-3 max-w-3xl"
  >
    <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0">
      <Bot className="w-4 h-4 text-primary-foreground" />
    </div>
    <div className="chat-bubble-ai px-5 py-4">
      <div className="flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-primary typing-dot-1" />
        <div className="w-2 h-2 rounded-full bg-primary typing-dot-2" />
        <div className="w-2 h-2 rounded-full bg-primary typing-dot-3" />
      </div>
    </div>
  </motion.div>
);

const MessageBubble = ({ message }: { message: ChatMessage }) => {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, x: isUser ? 10 : -10 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex items-start gap-3 max-w-3xl ${isUser ? "ml-auto flex-row-reverse" : ""}`}
    >
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
          isUser ? "bg-secondary" : "gradient-primary"
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-foreground" />
        ) : (
          <Bot className="w-4 h-4 text-primary-foreground" />
        )}
      </div>
      <div className="flex flex-col gap-1">
        <div className={isUser ? "chat-bubble-user" : "chat-bubble-ai"}>
          <p className="px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Inline table */}
        {message.table && (
          <div className="glass-panel overflow-hidden mt-2">
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {message.table.headers.map((h, i) => (
                      <th
                        key={i}
                        className="px-4 py-2.5 text-left text-xs font-semibold text-primary uppercase tracking-wider"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {message.table.rows.map((row, ri) => (
                    <tr key={ri} className="border-b border-border/50 last:border-0">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-4 py-2 text-foreground">
                          {cell?.toString() ?? ""}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <span className="text-[10px] text-muted-foreground/50 px-2">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </motion.div>
  );
};

const WelcomeScreen = () => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, ease: "easeOut" }}
    className="flex-1 flex flex-col items-center justify-center px-4 text-center"
  >
    <motion.div
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center mb-6 shadow-2xl animate-pulse-glow"
    >
      <Sparkles className="w-10 h-10 text-primary-foreground" />
    </motion.div>
    <h2 className="text-3xl font-bold gradient-text mb-3">Welcome to BPCL Excel Analytics Chatbot</h2>
    <p className="text-primary font-semibold max-w-md mb-8 drop-shadow-lg">
      Upload an Excel file and ask me anything about your data. I'll provide insights, summaries, and calculations instantly.
    </p>
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl w-full">
      {[
        { icon: "📊", title: "Data Analysis", desc: "Get summaries & statistics" },
        { icon: "🔍", title: "Smart Search", desc: "Find patterns in your data" },
        { icon: "📈", title: "Insights", desc: "Discover trends & outliers" },
      ].map((feature, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 + i * 0.1 }}
          className="glass-panel p-4 hover:glow-border transition-all duration-300"
        >
          <span className="text-2xl mb-2 block">{feature.icon}</span>
          <p className="text-sm font-semibold text-foreground">{feature.title}</p>
          <p className="text-xs text-muted-foreground">{feature.desc}</p>
        </motion.div>
      ))}
    </div>
  </motion.div>
);

const ChatArea = ({ messages, currentFile, onSendMessage, onUploadClick, isTyping }: ChatAreaProps) => {
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSendMessage(trimmed);
    setInput("");
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const target = e.target;
    target.style.height = "auto";
    target.style.height = Math.min(target.scrollHeight, 120) + "px";
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0">
      {/* Header bar */}
      <div className="px-6 py-4 border-b border-border glass-panel-strong rounded-none flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-primary" />
          <span className="font-semibold text-foreground">BPCL Excel Analytics Chatbot</span>
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        </div>
        {currentFile && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-medium text-primary">{currentFile.name}</span>
            <span className="text-xs text-muted-foreground">
              ({currentFile.selectedSheet} · {currentFile.rowCount} rows)
            </span>
          </motion.div>
        )}
      </div>

      {/* Messages */}
      {messages.length === 0 ? (
        <WelcomeScreen />
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-6 space-y-6">
          <AnimatePresence mode="popLayout">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </AnimatePresence>
          {isTyping && <TypingIndicator />}
          <div ref={chatEndRef} />
        </div>
      )}

      {/* Input bar */}
      <div className="px-6 py-4 border-t border-border">
        <div className="max-w-3xl mx-auto flex items-end gap-3">
          <button
            onClick={onUploadClick}
            className="shrink-0 w-10 h-10 rounded-xl bg-secondary hover:bg-secondary/80
              flex items-center justify-center text-muted-foreground hover:text-primary
              transition-all duration-200"
            title="Attach Excel file"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <div className="flex-1 glass-panel flex items-end glow-border">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={
                currentFile
                  ? `Ask about ${currentFile.name}...`
                  : "Upload an Excel file to start analyzing..."
              }
              rows={1}
              className="flex-1 bg-transparent px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground
                resize-none outline-none font-sans max-h-[120px]"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="shrink-0 m-1.5 w-9 h-9 rounded-lg gradient-primary flex items-center justify-center
                text-primary-foreground disabled:opacity-30 disabled:cursor-not-allowed
                hover:opacity-90 transition-all duration-200 active:scale-95"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;
