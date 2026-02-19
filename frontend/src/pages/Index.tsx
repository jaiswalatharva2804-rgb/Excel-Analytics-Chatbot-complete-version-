import { useState } from "react";
import ChatSidebar from "@/components/ChatSidebar";
import ChatArea from "@/components/ChatArea";
import FileUploadPanel from "@/components/FileUploadPanel";
import { useChatEngine } from "@/hooks/useChatEngine";
import { Menu, X } from "lucide-react";
import heroBg from "@/assets/hero-bg.jpg";

const Index = () => {
  const {
    sessions,
    activeSessionId,
    activeMessages,
    currentFile,
    isTyping,
    createNewChat,
    setActiveSessionId,
    deleteSession,
    setFile,
    sendMessage,
  } = useChatEngine();

  const [uploadOpen, setUploadOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="h-screen w-full flex overflow-hidden relative">
      {/* Background */}
      <div
        className="absolute inset-0 z-0 opacity-20"
        style={{
          backgroundImage: `url(${heroBg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      <div className="absolute inset-0 z-0 bg-background/85" />

      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 w-10 h-10 rounded-xl glass-panel-strong
          flex items-center justify-center text-foreground"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar */}
      <div
        className={`
          relative z-10 shrink-0 transition-all duration-300 ease-in-out
          ${sidebarOpen ? "w-72" : "w-0 overflow-hidden"}
          lg:w-72
        `}
      >
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={createNewChat}
          onSelectSession={setActiveSessionId}
          onDeleteSession={deleteSession}
          onUploadClick={() => setUploadOpen(true)}
        />
      </div>

      {/* Main chat area */}
      <div className="relative z-10 flex-1 min-w-0 flex flex-col">
        <ChatArea
          messages={activeMessages}
          currentFile={currentFile}
          onSendMessage={sendMessage}
          onUploadClick={() => setUploadOpen(true)}
          isTyping={isTyping}
        />
      </div>

      {/* Upload panel */}
      <FileUploadPanel
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onFileUploaded={setFile}
      />
    </div>
  );
};

export default Index;
