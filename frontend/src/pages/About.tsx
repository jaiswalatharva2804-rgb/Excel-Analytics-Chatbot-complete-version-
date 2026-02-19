import { motion } from "framer-motion";
import { ArrowLeft, Bot, Sparkles, FileSpreadsheet, Zap, Github, Users, Lock } from "lucide-react";
import { Link } from "react-router-dom";
import databytelogo from "../assets/databyte-logo.png";

const About = () => {
  return (
    <div className="min-h-screen w-full bg-background relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5" />
      
      {/* Large faded DataByte logo background - fixed position */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none overflow-hidden z-0">
        <img
          src={databytelogo}
          alt=""
          className="w-[1200px] h-[800px] object-contain opacity-[0.55]"
          aria-hidden="true"
        />
      </div>
      
      <div className="relative z-10 container mx-auto px-4 py-12 max-w-4xl">
        {/* Back button */}
        <Link to="/">
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="mb-8 flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Chat
          </motion.button>
        </Link>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center shadow-lg shadow-primary/30">
              <Bot className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-4xl font-bold gradient-text mb-4">
            About BPCL Excel Analytics Chatbot
          </h1>
          <p className="text-lg text-muted-foreground">
            Your intelligent assistant for data analysis and insights
          </p>
        </motion.div>

        {/* Content sections */}
        <div className="space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel p-6"
          >
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-primary" />
              What is BPCL Excel Analytics Chatbot?
            </h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              An intelligent chatbot for analyzing Excel/CSV data using natural language queries. <strong className="text-foreground">Runs 100% locally</strong> using Ollama LLMs and local embeddings - no external API calls required.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              Simply upload your Excel or CSV files, and ask questions in natural language. Our intelligent system will analyze your data and provide instant insights, summaries, and answers to your queries.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="glass-panel p-6 bg-primary/5 border-primary/20"
          >
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Lock className="w-6 h-6 text-primary" />
              Privacy & Local Processing
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              <strong className="text-foreground">🔒 Fully Local:</strong> Uses Ollama (local LLM) and sentence-transformers (local embeddings). Your data never leaves your machine, ensuring complete privacy and security.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-panel p-6"
          >
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Zap className="w-6 h-6 text-primary" />
              Key Features
            </h2>
            <ul className="space-y-3 text-muted-foreground">
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">🔒 Fully Local:</strong> 100% privacy with local LLM and embeddings - no external API calls</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">📊 Any Excel/CSV File:</strong> Load and analyze any data file format</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">🧠 Smart Routing:</strong> Automatically routes questions to the best analysis method</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">📝 Column Explanation:</strong> Properly explains all columns and data structure</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">📈 Trend Analysis:</strong> Analyze patterns and trends over time</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">🔍 Hybrid Analysis:</strong> Combines numerical and text analysis for comprehensive insights</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">Natural Language Queries:</strong> Ask questions in plain English, no complex formulas needed</span>
              </li>
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-panel p-6"
          >
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <FileSpreadsheet className="w-6 h-6 text-primary" />
              How It Works
            </h2>
            <ol className="space-y-4 text-muted-foreground">
              <li className="flex gap-4">
                <span className="text-2xl font-bold text-primary shrink-0">1</span>
                <div>
                  <strong className="text-foreground block mb-1">Upload Your File</strong>
                  Click the upload button and select your Excel or CSV file from your computer.
                </div>
              </li>
              <li className="flex gap-4">
                <span className="text-2xl font-bold text-primary shrink-0">2</span>
                <div>
                  <strong className="text-foreground block mb-1">Ask Questions</strong>
                  Type your questions in natural language, like "What is the average sales?" or "Show me the top 10 records."
                </div>
              </li>
              <li className="flex gap-4">
                <span className="text-2xl font-bold text-primary shrink-0">3</span>
                <div>
                  <strong className="text-foreground block mb-1">Get Insights</strong>
                  Receive instant, conversational responses with the information you need.
                </div>
              </li>
            </ol>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass-panel p-6"
          >
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Bot className="w-6 h-6 text-primary" />
              Query Types Supported
            </h2>
            <div className="space-y-3 text-muted-foreground">
              <div className="flex items-start gap-3">
                <span className="text-primary font-semibold shrink-0">Schema:</span>
                <span>"What columns are available?", "Explain all columns"</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-primary font-semibold shrink-0">SQL:</span>
                <span>"How many records?", "Average rating?", "Top 10 by score"</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-primary font-semibold shrink-0">Cluster:</span>
                <span>"Most common complaints?", "Main issues?"</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-primary font-semibold shrink-0">RAG:</span>
                <span>"Why are customers unhappy?", "Explain the issues"</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-primary font-semibold shrink-0">Trend:</span>
                <span>"Show the trend over time", "Monthly patterns"</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-primary font-semibold shrink-0">Hybrid:</span>
                <span>"Give me an overview", "Analyze discount trends"</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="glass-panel p-6"
          >
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Users className="w-6 h-6 text-primary" />
              Meet the Team
            </h2>
            <p className="text-muted-foreground mb-6">
              Built by a passionate team of developers dedicated to making data analysis accessible to everyone.
            </p>
            <div className="grid gap-4 md:grid-cols-3">
              <a
                href="https://github.com/jaiswalatharva2804"
                target="_blank"
                rel="noopener noreferrer"
                className="glass-panel p-4 hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Github className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    Atharva Jaiswal
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground">@jaiswalatharva2804</p>
              </a>

              <a
                href="https://github.com/HeC-KriS"
                target="_blank"
                rel="noopener noreferrer"
                className="glass-panel p-4 hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Github className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    Krishvinraam Mohan
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground">@HeC-KriS</p>
              </a>

              <a
                href="https://github.com/sai-rakesh-k"
                target="_blank"
                rel="noopener noreferrer"
                className="glass-panel p-4 hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Github className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    Sai Rakesh
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground">@sai-rakesh-k</p>
              </a>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="glass-panel p-6 bg-primary/5 border-primary/20"
          >
            <h2 className="text-2xl font-semibold mb-4">Powered by AI</h2>
            <p className="text-muted-foreground leading-relaxed">
              Our chatbot uses advanced artificial intelligence and natural language processing to understand your questions and analyze your data. Using Ollama for local LLM processing and FAISS for vector search, we ensure your data remains private while delivering powerful analytical insights. Whether you need simple summaries or complex analytical insights, BPCL Excel Analytics Chatbot makes data analysis accessible to everyone.
            </p>
          </motion.div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mt-12 text-center"
        >
          <Link to="/">
            <button className="px-8 py-3 gradient-primary text-primary-foreground font-semibold rounded-xl hover:opacity-90 transition-opacity">
              Start Analyzing Your Data
            </button>
          </Link>
        </motion.div>
      </div>
    </div>
  );
};

export default About;
