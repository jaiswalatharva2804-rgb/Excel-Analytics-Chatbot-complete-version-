import { useState, useCallback } from "react";
import type { UploadedFile } from "../components/FileUploadPanel";
import type { ChatMessage } from "../components/ChatArea";
import { api } from "../services/api";

interface ChatSession {
  id: string;
  name: string;
  fileName?: string;
  timestamp: Date;
  messages: ChatMessage[];
  file: UploadedFile | null;
}

const generateId = () => Math.random().toString(36).slice(2, 10);

export const useChatEngine = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: "default",
      name: "Welcome Chat",
      timestamp: new Date(),
      messages: [],
      file: null,
    },
  ]);
  const [activeSessionId, setActiveSessionId] = useState("default");
  const [isTyping, setIsTyping] = useState(false);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];

  const updateSession = useCallback(
    (id: string, updater: (s: ChatSession) => ChatSession) => {
      setSessions((prev) => prev.map((s) => (s.id === id ? updater(s) : s)));
    },
    []
  );

  const createNewChat = useCallback(() => {
    const newId = generateId();
    const newSession: ChatSession = {
      id: newId,
      name: "New Chat",
      timestamp: new Date(),
      messages: [],
      file: null,
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newId);
  }, []);

  const deleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== id);
        if (filtered.length === 0) {
          const fallback: ChatSession = {
            id: generateId(),
            name: "New Chat",
            timestamp: new Date(),
            messages: [],
            file: null,
          };
          setActiveSessionId(fallback.id);
          return [fallback];
        }
        if (activeSessionId === id) {
          setActiveSessionId(filtered[0].id);
        }
        return filtered;
      });
    },
    [activeSessionId]
  );

  const setFile = useCallback(
    (file: UploadedFile) => {
      const sysMsg: ChatMessage = {
        id: generateId(),
        role: "ai",
        content: `📁 **${file.name}** loaded successfully!\n\n• Sheet: **${file.selectedSheet}**\n• Rows: **${file.rowCount}**\n• Columns: **${file.headers.length}** (${file.headers.slice(0, 4).join(", ")}${file.headers.length > 4 ? "..." : ""})\n\nI'm ready to analyze your data. What would you like to know?`,
        timestamp: new Date(),
      };

      updateSession(activeSessionId, (s) => ({
        ...s,
        messages: [...s.messages, sysMsg],
        file,
        fileName: file.name,
        name: file.name.replace(/\.(xlsx|xls|csv)$/i, ""),
      }));
    },
    [activeSessionId, updateSession]
  );

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
        timestamp: new Date(),
      };

      updateSession(activeSessionId, (s) => ({
        ...s,
        messages: [...s.messages, userMsg],
      }));

      setIsTyping(true);

      try {
        // Call the real backend API
        const response = await api.ask(content);
        
        let aiContent = "";
        
        if (response.success && response.data?.answer) {
          aiContent = response.data.answer;
        } else {
          aiContent = response.error || "Sorry, I encountered an error processing your request.";
        }

        const aiMsg: ChatMessage = {
          id: generateId(),
          role: "ai",
          content: aiContent,
          timestamp: new Date(),
        };

        updateSession(activeSessionId, (s) => ({
          ...s,
          messages: [...s.messages, aiMsg],
        }));
      } catch (error) {
        const errorMsg: ChatMessage = {
          id: generateId(),
          role: "ai",
          content: "Sorry, I couldn't connect to the backend. Please make sure the backend server is running.",
          timestamp: new Date(),
        };

        updateSession(activeSessionId, (s) => ({
          ...s,
          messages: [...s.messages, errorMsg],
        }));
      } finally {
        setIsTyping(false);
      }
    },
    [activeSessionId, updateSession]
  );

  return {
    sessions: sessions.map(({ id, name, fileName, timestamp }) => ({ id, name, fileName, timestamp })),
    activeSessionId,
    activeMessages: activeSession.messages,
    currentFile: activeSession.file,
    isTyping,
    createNewChat,
    setActiveSessionId,
    deleteSession,
    setFile,
    sendMessage,
  };
};
