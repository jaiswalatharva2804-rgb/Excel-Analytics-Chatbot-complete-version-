import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import * as XLSX from "xlsx";
import { Upload, FileSpreadsheet, X, ChevronDown } from "lucide-react";
import { api } from "@/services/api";

export interface UploadedFile {
  name: string;
  sheets: string[];
  selectedSheet: string;
  data: any[][];
  headers: string[];
  rowCount: number;
  file?: File;
}

interface FileUploadPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onFileUploaded: (file: UploadedFile) => void;
}

const ACCEPTED_TYPES = {
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
  "text/csv": [".csv"],
};

const FileUploadPanel = ({ isOpen, onClose, onFileUploaded }: FileUploadPanelProps) => {
  const [parsedFile, setParsedFile] = useState<{
    name: string;
    workbook: XLSX.WorkBook;
    sheets: string[];
    file: File;
  } | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [sheetDropdownOpen, setSheetDropdownOpen] = useState(false);

  const processFile = (file: File) => {
    setError("");
    setIsProcessing(true);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array" });
        const sheets = workbook.SheetNames;

        setParsedFile({ name: file.name, workbook, sheets, file });
        setSelectedSheet(sheets[0]);
        setIsProcessing(false);
      } catch {
        setError("Failed to parse the file. Please ensure it's a valid Excel file.");
        setIsProcessing(false);
      }
    };
    reader.readAsArrayBuffer(file);
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    onDropAccepted: (files) => {
      processFile(files[0]);
    },
    onDropRejected: () => {
      setError("Only Excel files (.xlsx, .xls) and CSV files are allowed!");
    },
  });

  const handleConfirm = async () => {
    if (!parsedFile || !selectedSheet) return;

    console.log("Starting upload process...", parsedFile.name);
    setIsProcessing(true);
    setError("");

    try {
      // Upload file to backend
      console.log("Uploading file to backend...");
      const uploadResponse = await api.uploadFile(parsedFile.file);
      console.log("Upload response:", uploadResponse);

      if (!uploadResponse.success) {
        throw new Error(uploadResponse.error || "Upload failed");
      }

      // Get local data for preview
      const sheet = parsedFile.workbook.Sheets[selectedSheet];
      const jsonData = XLSX.utils.sheet_to_json<any[]>(sheet, { header: 1 });
      const headers = (jsonData[0] as string[]) || [];
      const dataRows = jsonData.slice(1);

      onFileUploaded({
        name: parsedFile.name,
        sheets: parsedFile.sheets,
        selectedSheet,
        data: dataRows,
        headers: uploadResponse.data?.columns || headers,
        rowCount: uploadResponse.data?.row_count || dataRows.length,
        file: parsedFile.file,
      });

      setParsedFile(null);
      setSelectedSheet("");
      setIsProcessing(false);
      onClose();
    } catch (err: any) {
      console.error("Upload error:", err);
      setError(err.message || "Failed to upload file");
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setParsedFile(null);
    setSelectedSheet("");
    setError("");
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="glass-panel-strong glow-border p-6 w-full max-w-lg mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center">
                  <Upload className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-foreground">Upload Excel File</h2>
                  <p className="text-sm text-muted-foreground">Supports .xlsx, .xls, .csv</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {!parsedFile ? (
              <>
                {/* Drop zone */}
                <div
                  {...getRootProps()}
                  className={`
                    relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
                    transition-all duration-300
                    ${isDragActive && !isDragReject ? "border-primary bg-primary/5 scale-[1.02]" : ""}
                    ${isDragReject ? "border-destructive bg-destructive/5" : ""}
                    ${!isDragActive ? "border-border hover:border-primary/50 hover:bg-secondary/30" : ""}
                  `}
                >
                  <input {...getInputProps()} />
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center animate-float">
                      <FileSpreadsheet className="w-8 h-8 text-primary" />
                    </div>
                    {isDragReject ? (
                      <p className="text-destructive font-medium">This file type is not supported!</p>
                    ) : isDragActive ? (
                      <p className="text-primary font-medium">Drop your Excel file here...</p>
                    ) : (
                      <>
                        <p className="text-foreground font-medium">
                          Drag & drop your Excel file here
                        </p>
                        <p className="text-sm text-muted-foreground">
                          or click to browse
                        </p>
                      </>
                    )}
                  </div>
                </div>

                {isProcessing && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-primary">
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm">Processing file...</span>
                  </div>
                )}
              </>
            ) : (
              <>
                {/* File preview */}
                <div className="glass-panel p-4 mb-4">
                  <div className="flex items-center gap-3 mb-3">
                    <FileSpreadsheet className="w-5 h-5 text-primary" />
                    <span className="font-medium text-foreground truncate">{parsedFile.name}</span>
                    <button
                      onClick={handleReset}
                      className="ml-auto text-muted-foreground hover:text-destructive transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {parsedFile.sheets.length} sheet{parsedFile.sheets.length > 1 ? "s" : ""} found
                  </p>
                </div>

                {/* Sheet selector */}
                {parsedFile.sheets.length > 1 && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                      Select Sheet
                    </label>
                    <div className="relative">
                      <button
                        onClick={() => setSheetDropdownOpen(!sheetDropdownOpen)}
                        className="w-full glass-panel p-3 text-left text-foreground flex items-center justify-between hover:bg-secondary/50 transition-colors"
                      >
                        <span>{selectedSheet}</span>
                        <ChevronDown className={`w-4 h-4 transition-transform ${sheetDropdownOpen ? "rotate-180" : ""}`} />
                      </button>
                      <AnimatePresence>
                        {sheetDropdownOpen && (
                          <motion.div
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -4 }}
                            className="absolute top-full left-0 right-0 mt-1 glass-panel-strong z-10 overflow-hidden"
                          >
                            {parsedFile.sheets.map((sheet) => (
                              <button
                                key={sheet}
                                onClick={() => {
                                  setSelectedSheet(sheet);
                                  setSheetDropdownOpen(false);
                                }}
                                className={`w-full p-3 text-left text-sm transition-colors ${
                                  selectedSheet === sheet
                                    ? "bg-primary/10 text-primary"
                                    : "text-foreground hover:bg-secondary/50"
                                }`}
                              >
                                {sheet}
                              </button>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                )}

                {/* Confirm button */}
                <button
                  onClick={handleConfirm}
                  disabled={isProcessing}
                  className="w-full gradient-primary text-primary-foreground font-semibold py-3 rounded-xl
                    hover:opacity-90 transition-opacity animate-pulse-glow disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? "Processing..." : "Start Analyzing"}
                </button>
              </>
            )}

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default FileUploadPanel;
