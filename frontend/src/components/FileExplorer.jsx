import LanguageIcon from "./LanguageIcon";

function FileExplorer({
  files,
  activeFile,
  onFileSelect,
  onCreateFile,
  onDeleteFile,
  onRenameFile,
  workspaces = [],
  selectedWorkspaceId,
  onWorkspaceChange,
  onCreateWorkspace,
  workspaceLoading = false,
  workspaceError = "",
  projects = [],
  selectedProjectId,
  onProjectChange,
  onCreateProject,
  projectLoading = false,
  projectError = "",
}) {
  return (
    <aside className="file-explorer">
      <div className="explorer-header">
        <span>EXPLORER</span>
        <button type="button" title="New file" onClick={onCreateFile}>
          +
        </button>
      </div>

      <div className="explorer-management">
        <div className="explorer-section-title">WORKSPACE</div>

        {workspaceLoading ? (
          <div className="explorer-status">Loading...</div>
        ) : (
          <>
            {workspaces.length > 0 ? (
              <select
                className="explorer-select"
                value={selectedWorkspaceId || ""}
                onChange={onWorkspaceChange}
              >
                {workspaces.map((workspace) => (
                  <option key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </option>
                ))}
              </select>
            ) : (
              <div className="explorer-status">No workspace</div>
            )}

            <form
              className="explorer-create-form"
              onSubmit={onCreateWorkspace}
            >
              <input
                className="explorer-input"
                name="name"
                placeholder="New workspace"
                autoComplete="off"
              />
              <button type="submit" className="explorer-create-button">
                +
              </button>
            </form>

            {workspaceError && (
              <div className="explorer-error">{workspaceError}</div>
            )}
          </>
        )}

        <div className="explorer-section-title explorer-project-title">
          PROJECT
        </div>

        {projectLoading ? (
          <div className="explorer-status">Loading...</div>
        ) : (
          <>
            {projects.length > 0 ? (
              <select
                className="explorer-select"
                value={selectedProjectId || ""}
                onChange={onProjectChange}
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            ) : (
              <div className="explorer-status">No project</div>
            )}

            <form
              className="explorer-create-form"
              onSubmit={onCreateProject}
            >
              <input
                className="explorer-input"
                name="name"
                placeholder="New project"
                autoComplete="off"
              />
              <button type="submit" className="explorer-create-button">
                +
              </button>
            </form>

            {projectError && (
              <div className="explorer-error">{projectError}</div>
            )}
          </>
        )}
      </div>

      <div className="explorer-files-title">FILES</div>

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
              <span className="file-icon">
                <LanguageIcon language={file.language} />
              </span>
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

