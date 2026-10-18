import React, { useRef, useState, DragEvent } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function FileUpload({ onFileSelect, disabled }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSelect(file);
    }
  };

  const validateAndSelect = (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "txt") {
      alert("Unsupported file type. Please upload a PDF or TXT file.");
      return;
    }
    if (file.size === 0) {
      alert("The uploaded file is empty.");
      return;
    }
    onFileSelect(file);
  };

  const loadSampleContract = () => {
    const sampleText = `Company Name: Golden Brown Technologies
CEO: Rahul Sharma
Founded: 2024
Headquarters: Bengaluru
Annual leave: 24 days
Notice period: 30 days
`;
    const blob = new Blob([sampleText], { type: "text/plain" });
    const file = new File([blob], "test_document.txt", { type: "text/plain" });
    onFileSelect(file);
  };

  return (
    <div className="upload-wrapper">
      <div
        className={`dropzone-card ${isDragging ? "active-drag" : ""} ${disabled ? "disabled" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              validateAndSelect(e.target.files[0]);
            }
          }}
          disabled={disabled}
        />

        <div className="dropzone-icon">📄</div>
        <h3 className="dropzone-heading">Upload PDF / TXT</h3>
        <p className="dropzone-sub">
          Drag &amp; drop your agreement here, or <span>Browse files</span>
        </p>
        <span className="supported-badge">Supported: PDF, TXT (up to 50 MB)</span>
      </div>

      <div className="sample-quick-bar">
        <span className="sample-title">⚡ Quick Test:</span>
        <button
          type="button"
          className="sample-action-btn"
          onClick={(e) => {
            e.stopPropagation();
            loadSampleContract();
          }}
          disabled={disabled}
        >
          Load Section 32 Benchmark Contract (test_document.txt)
        </button>
      </div>
    </div>
  );
}
