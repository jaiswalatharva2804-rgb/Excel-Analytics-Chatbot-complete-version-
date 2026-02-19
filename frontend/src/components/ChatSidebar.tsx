import { motion } from "framer-motion";
import {
  Plus,
  Upload,
  FileSpreadsheet,
  Settings,
  MessageSquare,
  Trash2,
} from "lucide-react";
import databytelogo from "../assets/databyte-logo.png";

interface ChatSession {
  id: string;
  name: string;
  fileName?: string;
  timestamp: Date;
}

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onUploadClick: () => void;
}

const ChatSidebar = ({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onUploadClick,
}: ChatSidebarProps) => {
  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="w-72 h-full glass-panel-strong border-r border-border flex flex-col"
    >
      {/* Logo */}
      <div className="p-5 border-b border-border">
        <div className="flex items-center gap-3">
          <img
            src={databytelogo}
            alt="DataByte logo"
            className="w-10 h-10 object-contain"
          />
          <div>
            <h1 className="text-lg font-bold gradient-text">Excel Analytics Chatbot</h1>
            <p className="text-xs text-muted-foreground">AI Analytics</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="p-4 space-y-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-secondary hover:bg-secondary/80
            text-foreground font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>

        <button
          onClick={onUploadClick}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl gradient-primary
            text-primary-foreground font-medium transition-all duration-200 hover:opacity-90
            hover:scale-[1.02] active:scale-[0.98] animate-pulse-glow"
        >
          <Upload className="w-4 h-4" />
          Upload Excel
        </button>
      </div>

      {/* File History */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 pb-4">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">
          Recent Chats
        </p>
        <div className="space-y-1">
          {sessions.length === 0 ? (
            <div className="text-center py-8 px-4">
              <MessageSquare className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground/50">No chats yet</p>
            </div>
          ) : (
            sessions.map((session, index) => (
              <motion.button
                key={session.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onSelectSession(session.id)}
                className={`
                  w-full group flex items-center gap-3 px-3 py-2.5 rounded-lg text-left
                  transition-all duration-200
                  ${
                    activeSessionId === session.id
                      ? "bg-primary/10 border border-primary/20 text-foreground"
                      : "hover:bg-secondary/50 text-muted-foreground hover:text-foreground"
                  }
                `}
              >
                {session.fileName ? (
                  <FileSpreadsheet className="w-4 h-4 text-primary shrink-0" />
                ) : (
                  <MessageSquare className="w-4 h-4 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{session.name}</p>
                  {session.fileName && (
                    <p className="text-xs text-muted-foreground truncate">{session.fileName}</p>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10
                    text-muted-foreground hover:text-destructive transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </motion.button>
            ))
          )}
        </div>
      </div>

      {/* Settings */}
      <div className="p-4 border-t border-border">
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground
          hover:text-foreground hover:bg-secondary/50 transition-all duration-200">
          <Settings className="w-4 h-4" />
          <span className="text-sm">Settings</span>
        </button>
      </div>
    </motion.aside>
  );
};

export default ChatSidebar;
