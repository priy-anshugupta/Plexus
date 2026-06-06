"use client";

import React, { useEffect, useRef } from "react";
import MonacoEditor, { EditorProps } from "@monaco-editor/react";

interface CodeViewerProps {
  code: string;
  filePath: string;
  highlightLine?: number;
}

export default function CodeViewer({ code, filePath, highlightLine }: CodeViewerProps) {
  const editorRef = useRef<any>(null);

  // Detect file language based on file extension
  const getLanguage = (path: string) => {
    const ext = path.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "py": return "python";
      case "js":
      case "jsx": return "javascript";
      case "ts":
      case "tsx": return "typescript";
      case "yml":
      case "yaml": return "yaml";
      case "json": return "json";
      case "sql": return "sql";
      case "sh": return "shell";
      case "go": return "go";
      case "md": return "markdown";
      default: return "plaintext";
    }
  };

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Apply custom styling themes if needed
    monaco.editor.defineTheme("plexus-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#0b0e14",
        "editor.lineHighlightBackground": "#1e293b50",
      },
    });
    monaco.editor.setTheme("plexus-dark");

    // Scroll to and highlight targeted vulnerability line
    if (highlightLine) {
      scrollToLine(highlightLine, monaco);
    }
  };

  const scrollToLine = (line: number, monacoInstance?: any) => {
    if (!editorRef.current) return;
    
    const editor = editorRef.current;
    
    // Scroll editor to centered line
    editor.revealLineInCenter(line);
    editor.setPosition({ lineNumber: line, column: 1 });
    editor.focus();

    // Add visual decoration/marker to line
    const monaco = monacoInstance || (window as any).monaco;
    if (monaco) {
      // Clear previous decorations if any
      const currentDecorations = editor.getValueDecorations() || [];
      const decoIds = currentDecorations
        .filter((d: any) => d.options.className === "vuln-line-highlight")
        .map((d: any) => d.id);
      
      editor.deltaDecorations(decoIds, [
        {
          range: new monaco.Range(line, 1, line, 1),
          options: {
            isWholeLine: true,
            className: "vuln-line-highlight",
            glyphMarginClassName: "vuln-glyph-margin",
            hoverMessage: { value: "⚠️ AI-flagged vulnerability location" },
          },
        },
      ]);
    }
  };

  useEffect(() => {
    if (editorRef.current && highlightLine) {
      scrollToLine(highlightLine);
    }
  }, [highlightLine]);

  return (
    <div className="rounded-xl overflow-hidden border border-white/5 bg-[#0b0e14] h-full flex flex-col min-h-[400px]">
      {/* File Header */}
      <div className="bg-slate-950 px-4 py-2.5 border-b border-white/5 flex items-center justify-between font-mono text-xs text-slate-400">
        <span className="truncate">{filePath || "unnamed_snippet"}</span>
        <span className="bg-slate-900 px-2 py-0.5 rounded border border-white/5 uppercase">
          {getLanguage(filePath)}
        </span>
      </div>

      {/* Monaco viewport container */}
      <div className="flex-1 min-h-0">
        <MonacoEditor
          height="100%"
          language={getLanguage(filePath)}
          value={code}
          theme="vs-dark"
          onMount={handleEditorDidMount}
          options={{
            readOnly: true,
            minimap: { enabled: true },
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            fontSize: 13,
            fontFamily: "var(--font-mono), monospace",
            cursorBlinking: "smooth",
            folding: true,
            glyphMargin: true,
            scrollbar: {
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
            }
          }}
        />
      </div>

      {/* CSS injecting block for Monaco decorations */}
      <style jsx global>{`
        .vuln-line-highlight {
          background-color: rgba(244, 63, 94, 0.15) !important;
          border-left: 3px solid #f43f5e !important;
        }
        .vuln-glyph-margin {
          background: #f43f5e;
          width: 5px !important;
          height: 100%;
        }
      `}</style>
    </div>
  );
}
