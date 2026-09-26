import LanguageIcon from "./LanguageIcon";
function FileExplorer({ files, activeFile, onFileSelect, onCreateFile, onDeleteFile, onRenameFile }) {
  return (
    <aside className="file-explorer">
      <div className="explorer-header">
        <span>EXPLORER</span>
        <button
          type="button"
          title="New file"
          onClick={onCreateFile}
        >
          +
        </button>
      </div>

      <div className="project-name">
        <span className="folder-icon">&gt;</span>
        <span>codecollab</span>
      </div>

      <div className="file-list">
        {files.map((file) => (
          <div
            key={file.id}
            className={`file-item ${
              activeFile?.id === file.id ? "active" : ""
            }`}
          >
            <button
              type="button"
              className="file-select-button"
              onClick={() => onFileSelect(file)}
            >
              <span className="file-icon"><LanguageIcon language={file.language} /></span>
              <span>{file.name}</span>
            </button>

            <button
              type="button"
              className="file-rename-button"
              title={`Rename ${file.name}`}
              onClick={() => onRenameFile(file)}
            >
              R
            </button>

            <button
              type="button"
              className="file-delete-button"
              title={`Delete ${file.name}`}
              onClick={() => onDeleteFile(file)}
            >
              X
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default FileExplorer;










