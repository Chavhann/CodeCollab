import Editor from "@monaco-editor/react";
import LanguageIcon from "./LanguageIcon";

function CodeEditor({ file, onChange, onSave, saving }) {
  return (
    <div className="code-editor">
      <div
        className="editor-tab"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <LanguageIcon language={file?.language} className="tab-language-icon" />
          <span>{file?.name || "No file selected"}</span>
        </div>

        {file && (
          <button
            type="button"
            onClick={onSave}
            disabled={saving}
            style={{
              padding: "5px 12px",
              border: "1px solid #30363d",
              borderRadius: "5px",
              background: saving ? "#21262d" : "#238636",
              color: "#ffffff",
              fontSize: "12px",
              fontWeight: "600",
              cursor: saving ? "wait" : "pointer",
            }}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        )}
      </div>

      <div className="monaco-container">
        <Editor
          height="100%"
          language={file?.language || "plaintext"}
          value={file?.content || ""}
          onChange={(value) => onChange(value ?? "")}
          theme="vs-dark"
          options={{
            automaticLayout: true,
            minimap: { enabled: true },
            fontSize: 14,
            fontFamily: "Consolas, 'Courier New', monospace",
            lineNumbers: "on",
            wordWrap: "on",
            tabSize: 4,
            scrollBeyondLastLine: false,
            padding: {
              top: 12,
              bottom: 12,
            },
          }}
        />
      </div>
    </div>
  );
}

export default CodeEditor;



