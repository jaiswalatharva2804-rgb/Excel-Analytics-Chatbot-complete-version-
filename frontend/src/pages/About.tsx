import { motion } from "framer-motion";
import { ArrowLeft, Bot, Sparkles, FileSpreadsheet, Zap } from "lucide-react";
import { Link } from "react-router-dom";

const About = () => {
  return (
    <div className="min-h-screen w-full bg-background relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5" />
      
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
            <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center">
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
            <p className="text-muted-foreground leading-relaxed">
              BPCL Excel Analytics Chatbot is an AI-powered tool designed to help you analyze and understand your Excel data effortlessly. Simply upload your Excel or CSV files, and ask questions in natural language. Our intelligent system will analyze your data and provide instant insights, summaries, and answers to your queries.
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
                <span><strong className="text-foreground">Natural Language Queries:</strong> Ask questions in plain English, no complex formulas needed</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">Instant Analysis:</strong> Get immediate insights from your data with AI-powered analytics</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">Multiple File Support:</strong> Works with Excel files (.xlsx, .xls) and CSV files</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">Smart Responses:</strong> Conversational AI that explains results in clear, easy-to-understand language</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <span><strong className="text-foreground">Data Visualization:</strong> View your data in organized tables and understand patterns quickly</span>
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
            className="glass-panel p-6 bg-primary/5 border-primary/20"
          >
            <h2 className="text-2xl font-semibold mb-4">Powered by AI</h2>
            <p className="text-muted-foreground leading-relaxed">
              Our chatbot uses advanced artificial intelligence and natural language processing to understand your questions and analyze your data. Whether you need simple summaries or complex analytical insights, BPCL Excel Analytics Chatbot makes data analysis accessible to everyone.
            </p>
          </motion.div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
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
