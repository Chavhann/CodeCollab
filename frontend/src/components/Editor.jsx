import { useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import LanguageIcon from "./LanguageIcon";

function CodeEditor({ file, onChange, onSave, saving, onCursorChange, presence = [] }) {
  const editorRef = useRef(null);
  const decorationsRef = useRef([]);
  const monacoRef = useRef(null);
  useEffect(() => {
    const editor = editorRef.current;

    if (!editor || !monacoRef.current) {
      return;
    }

    const decorations = [];

    presence.forEach((collaborator, index) => {
      if (!collaborator.cursor) {
        return;
      }

      const line = Math.max(1, collaborator.cursor.line + 1);
      const column = Math.max(1, collaborator.cursor.column + 1);
      const cursorClass = `remote-cursor-${index % 6}`;
      const selectionClass = `remote-selection-${index % 6}`;

      decorations.push({
        range: new monacoRef.current.Range(line, column, line, column),
        options: {
          beforeContentClassName: cursorClass,
          hoverMessage: {
            value: `**${collaborator.username || "Collaborator"}**`,
          },
        },
      });

      if (collaborator.selection_start && collaborator.selection_end) {
        const startLine = Math.max(1, collaborator.selection_start.line + 1);
        const startColumn = Math.max(1, collaborator.selection_start.column + 1);
        const endLine = Math.max(1, collaborator.selection_end.line + 1);
        const endColumn = Math.max(1, collaborator.selection_end.column + 1);

        decorations.push({
          range: new monacoRef.current.Range(
            startLine,
            startColumn,
            endLine,
            endColumn,
          ),
          options: {
            className: selectionClass,
            hoverMessage: {
              value: `**${collaborator.username || "Collaborator"}**`,
            },
          },
        });
      }
    });

    decorationsRef.current = editor.deltaDecorations(
      decorationsRef.current,
      decorations,
    );
  }, [presence]);
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
          onMount={(editor, monaco) => {
            editorRef.current = editor;
            monacoRef.current = monaco;
            editor.onDidChangeCursorPosition((event) => {
              onCursorChange?.({
                line: event.position.lineNumber - 1,
                column: event.position.column - 1,
              });
            });
            editor.onDidChangeCursorSelection((event) => {
              const selection = event.selection;
              onCursorChange?.({
                line: selection.positionLineNumber - 1,
                column: selection.positionColumn - 1,
                selectionStart: {
                  line: selection.selectionStartLineNumber - 1,
                  column: selection.selectionStartColumn - 1,
                },
                selectionEnd: {
                  line: selection.positionLineNumber - 1,
                  column: selection.positionColumn - 1,
                },
              });
            });
          }}
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








