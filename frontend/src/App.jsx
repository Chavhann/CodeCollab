import { useEffect, useState } from "react";
import Editor from "./components/Editor";
import FileExplorer from "./components/FileExplorer";
import Header from "./components/Header";
import useCollaboration from "./hooks/useCollaboration";
import Login from "./components/auth/Login";
import { getCurrentUser, logoutUser } from "./api/auth";
import { createFile, listFiles, updateFile, deleteFile } from "./api/files";
import { createWorkspace, listWorkspaces, createProject, listProjects } from "./api/workspace";
import "./styles.css";

const initialFiles = [
  {
    id: 1,
    name: "main.py",
    language: "python",
    content: `def hello():
    print("Hello, CodeCollab!")

hello()
`,
  },
  {
    id: 2,
    name: "app.py",
    language: "python",
    content: `from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World"
`,
  },
  {
    id: 3,
    name: "README.md",
    language: "markdown",
    content: `# CodeCollab

Real-time collaborative development workspace.
`,
  },
];

function App() {
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  const [workspaces, setWorkspaces] = useState([]);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [workspaceError, setWorkspaceError] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDescription, setWorkspaceDescription] = useState("");
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(null);

  const [projects, setProjects] = useState([]);
  const [projectLoading, setProjectLoading] = useState(false);
  const [projectError, setProjectError] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [creatingProject, setCreatingProject] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  const [files, setFiles] = useState(initialFiles);
  const [activeFileId, setActiveFileId] = useState(1);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState("");
  const [creatingFile, setCreatingFile] = useState(false);
  const [savingFile, setSavingFile] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("codecollab_token");

    if (!token) {
      setAuthChecking(false);
      return;
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => {
        logoutUser();
        setUser(null);
      })
      .finally(() => {
        setAuthChecking(false);
      });
  }, []);

  useEffect(() => {
    if (!user) {
      setWorkspaces([]);
      setSelectedWorkspaceId(null);
      return;
    }

    setWorkspaceLoading(true);
    setWorkspaceError("");

    listWorkspaces()
      .then((data) => {
        setWorkspaces(data);

        if (data.length > 0) {
          setSelectedWorkspaceId(data[0].id);
        }
      })
      .catch((error) => {
        setWorkspaceError(error.message || "Failed to load workspaces");
      })
      .finally(() => {
        setWorkspaceLoading(false);
      });
  }, [user]);

  useEffect(() => {
    if (!selectedWorkspaceId) {
      setProjects([]);
      setSelectedProjectId(null);
      return;
    }

    setProjectLoading(true);
    setProjectError("");

    listProjects(selectedWorkspaceId)
      .then((data) => {
        setProjects(data);

        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        } else {
          setSelectedProjectId(null);
        }
      })
      .catch((error) => {
        setProjectError(error.message || "Failed to load projects");
      })
      .finally(() => {
        setProjectLoading(false);
      });
  }, [selectedWorkspaceId]);

  useEffect(() => {
    if (!selectedProjectId) {
      setFiles([]);
      setActiveFileId(null);
      return;
    }

    setFileLoading(true);
    setFileError("");

    listFiles(selectedProjectId)
      .then((data) => {
        const formattedFiles = data.map((file) => ({
          id: file.id,
          name: file.path.split("/").pop() || file.path,
          path: file.path,
          language: file.language || "plaintext",
          content: file.content || "",
          versionNumber: file.version_number,
        }));

        setFiles(formattedFiles);
        setActiveFileId(
          formattedFiles.length > 0 ? formattedFiles[0].id : null
        );
      })
      .catch((error) => {
        setFileError(error.message || "Failed to load project files");
        setFiles([]);
        setActiveFileId(null);
      })
      .finally(() => {
        setFileLoading(false);
      });
  }, [selectedProjectId]);

  const handleCreateWorkspace = async (event) => {
    event.preventDefault();

    const name = workspaceName.trim();

    if (!name) {
      setWorkspaceError("Workspace name is required.");
      return;
    }

    setCreatingWorkspace(true);
    setWorkspaceError("");

    try {
      const workspace = await createWorkspace({
        name,
        description: workspaceDescription.trim() || undefined,
      });

      setWorkspaces((current) => [workspace, ...current]);
      setSelectedWorkspaceId(workspace.id);
      setWorkspaceName("");
      setWorkspaceDescription("");
    } catch (error) {
      setWorkspaceError(error.message || "Failed to create workspace");
    } finally {
      setCreatingWorkspace(false);
    }
  };

  const handleCreateProject = async (event) => {
    event.preventDefault();

    const name = projectName.trim();

    if (!selectedWorkspaceId) {
      setProjectError("Select a workspace first.");
      return;
    }

    if (!name) {
      setProjectError("Project name is required.");
      return;
    }

    setCreatingProject(true);
    setProjectError("");

    try {
      const project = await createProject(selectedWorkspaceId, {
        name,
        description: projectDescription.trim() || undefined,
      });

      setProjects((current) => [project, ...current]);
      setSelectedProjectId(project.id);
      setProjectName("");
      setProjectDescription("");
    } catch (error) {
      setProjectError(error.message || "Failed to create project");
    } finally {
      setCreatingProject(false);
    }
  };

  const handleCreateFile = async () => {
    if (!selectedProjectId) {
      setFileError("Select a project first.");
      return;
    }

    const path = window.prompt("Enter file name:", "main.py");

    if (path === null) {
      return;
    }

    const trimmedPath = path.trim();

    if (!trimmedPath) {
      setFileError("File name is required.");
      return;
    }

    if (files.some((file) => file.path === trimmedPath)) {
      setFileError("A file with this name already exists.");
      return;
    }

    const extension = trimmedPath.includes(".")
      ? trimmedPath.split(".").pop().toLowerCase()
      : "";

    const languageMap = {
      py: "python",
      js: "javascript",
      jsx: "javascript",
      ts: "typescript",
      tsx: "typescript",
      html: "html",
      css: "css",
      json: "json",
      md: "markdown",
      java: "java",
      c: "c",
      cpp: "cpp",
      ipynb: "jupyter",
    };

    const language = languageMap[extension] || "plaintext";

    setCreatingFile(true);
    setFileError("");

    try {
      const file = await createFile(selectedProjectId, {
        path: trimmedPath,
        language,
        content: "",
      });

      const formattedFile = {
        id: file.id,
        name: file.path.split("/").pop() || file.path,
        path: file.path,
        language: file.language || language,
        content: file.content || "",
        versionNumber: file.version_number,
      };

      setFiles((current) => [...current, formattedFile]);
      setActiveFileId(formattedFile.id);
    } catch (error) {
      setFileError(error.message || "Failed to create file");
    } finally {
      setCreatingFile(false);
    }
  };

  const handleRenameFile = async (file) => {
    if (!selectedProjectId || !file) {
      return;
    }

    const newName = window.prompt(`Rename ${file.name} to:`, file.name);

    if (!newName || newName.trim() === file.name) {
      return;
    }

    const trimmedName = newName.trim();

    if (trimmedName.includes("/") || trimmedName.includes("\\")) {
      setFileError("File name cannot contain / or \.");
      return;
    }

    const newPath = file.path.includes("/")
      ? `${file.path.substring(0, file.path.lastIndexOf("/") + 1)}${trimmedName}`
      : trimmedName;

    if (files.some((currentFile) => currentFile.id !== file.id && currentFile.name === trimmedName)) {
      setFileError("A file with this name already exists");
      return;
    }

    setFileError("");

    try {
      const updatedFile = await updateFile(selectedProjectId, file.id, {
        content: file.content,
        language: file.language,
        path: newPath,
      });

      setFiles((current) =>
        current.map((currentFile) =>
          currentFile.id === file.id
            ? {
                ...currentFile,
                name: updatedFile.path.split("/").pop(),
                path: updatedFile.path,
                language: updatedFile.language,
                content: updatedFile.content,
                versionNumber: updatedFile.version_number,
              }
            : currentFile
        )
      );
    } catch (error) {
      setFileError(error.message || "Failed to rename file");
    }
  };
  const handleDeleteFile = async (file) => {
    if (!selectedProjectId || !file) {
      return;
    }

    const confirmed = window.confirm(`Delete ${file.name}?`);

    if (!confirmed) {
      return;
    }

    setFileError("");

    try {
      console.log("Deleting file:", file.id, "from project:", selectedProjectId); await deleteFile(selectedProjectId, file.id); console.log("File deleted successfully:", file.id);

      setFiles((current) => {
        const remainingFiles = current.filter(
          (currentFile) => currentFile.id !== file.id
        );

        if (file.id === activeFileId) {
          setActiveFileId(
            remainingFiles.length > 0 ? remainingFiles[0].id : null
          );
        }

        return remainingFiles;
      });
    } catch (error) {
      setFileError(error.message || "Failed to delete file");
    }
  };

  const handleSaveFile = async () => {
    if (!selectedProjectId || !activeFile) {
      return;
    }

    setSavingFile(true);
    setFileError("");

    try {
      const updatedFile = await updateFile(
        selectedProjectId,
        activeFile.id,
        {
          content: activeFile.content,
          language: activeFile.language,
        }
      );

      setFiles((current) =>
        current.map((file) =>
          file.id === activeFile.id
            ? {
                ...file,
                content: updatedFile.content,
                language: updatedFile.language || file.language,
                versionNumber: updatedFile.version_number,
              }
            : file
        )
      );
    } catch (error) {
      setFileError(error.message || "Failed to save file");
    } finally {
      setSavingFile(false);
    }
  };

  const handleWorkspaceChange = (event) => {
    setSelectedWorkspaceId(Number(event.target.value));
  };

  const handleProjectChange = (event) => {
    setSelectedProjectId(Number(event.target.value));
  };

  const activeFile =
    files.find((file) => file.id === activeFileId) ?? null;

  const collaboration = useCollaboration({
    projectId: selectedProjectId,
    fileId: activeFileId,
    initialContent: activeFile?.content || "",
    onRemoteContent: (content) => {
      setFiles((currentFiles) =>
        currentFiles.map((file) =>
          file.id === activeFileId
            ? { ...file, content }
            : file
        )
      );
    },
  });

  const handleFileSelect = (file) => {
    setActiveFileId(file.id);
  };

  const handleEditorChange = (content) => {
    setFiles((currentFiles) =>
      currentFiles.map((file) =>
        file.id === activeFileId
          ? {
              ...file,
              content,
            }
          : file
      )
    );

    collaboration.handleLocalChange(content);
  };

  const handleLogout = () => {
    logoutUser();
    setUser(null);
  };

  if (authChecking) {
    return (
      <div className="auth-page">
        <div className="auth-loading">Loading CodeCollab...</div>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <div className="app-shell">
      <Header user={user} onLogout={handleLogout} connectionStatus={collaboration.connectionStatus} presence={collaboration.presence} />

      <div className="workspace">
        <FileExplorer
          files={files}
          activeFile={activeFile}
          onFileSelect={handleFileSelect}
          onCreateFile={handleCreateFile}
          onDeleteFile={handleDeleteFile}
          onRenameFile={handleRenameFile}
          workspaces={workspaces}
          selectedWorkspaceId={selectedWorkspaceId}
          onWorkspaceChange={handleWorkspaceChange}
          onCreateWorkspace={handleCreateWorkspace}
          workspaceLoading={workspaceLoading}
          workspaceError={workspaceError}
          projects={projects}
          selectedProjectId={selectedProjectId}
          onProjectChange={handleProjectChange}
          onCreateProject={handleCreateProject}
          projectLoading={projectLoading}
          projectError={projectError}
        />

        <main className="editor-area">
          {fileLoading ? (
            <div className="auth-loading">Loading project files...</div>
          ) : activeFile ? (
            <Editor
              file={activeFile}
              onChange={handleEditorChange}
              onSave={handleSaveFile}
              saving={savingFile}
            />
          ) : (
            <div className="auth-loading">
              Create a file to start coding.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;



























