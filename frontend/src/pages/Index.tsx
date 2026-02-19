import { useState } from "react";
import ChatSidebar from "@/components/ChatSidebar";
import ChatArea from "@/components/ChatArea";
import FileUploadPanel from "@/components/FileUploadPanel";
import { useChatEngine } from "@/hooks/useChatEngine";
import { Menu, X } from "lucide-react";
import heroBg from "@/assets/hero-bg.jpg";
import auroraBg from "@/assets/aurora-bg.jpg";
import databytelogo from "@/assets/databyte-logo.png";

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
      {/* Layer 1: Main Aurora Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url(${auroraBg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      
      {/* Layer 2: Subtle overlay */}
      <div className="absolute inset-0 z-0 bg-background/40" />

      {/* Large faded DataByte logo background with glow effect - centered in main content area */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none overflow-hidden z-0" style={{ marginLeft: '18rem' }}>
        <div className="relative">
          {/* Glow layers */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-[1100px] h-[550px] rounded-full bg-primary/3 blur-3xl"></div>
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-[850px] h-[420px] rounded-full bg-accent/5 blur-2xl"></div>
          </div>
          {/* Logo with subtle shadow */}
          <img
            src={databytelogo}
            alt=""
            className="relative w-[1100px] h-[550px] object-contain opacity-[0.04]"
            style={{ 
              filter: 'drop-shadow(0 0 30px rgba(16,185,129,0.2)) drop-shadow(0 0 60px rgba(20,184,166,0.15)) drop-shadow(0 10px 20px rgba(0,0,0,0.3))'
            }}
            aria-hidden="true"
          />
        </div>
      </div>

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
