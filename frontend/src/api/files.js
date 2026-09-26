import { apiRequest } from "./client";

export async function listFiles(projectId) {
  return apiRequest(`/projects/${projectId}/files`);
}

export async function getFile(projectId, fileId) {
  return apiRequest(`/projects/${projectId}/files/${fileId}`);
}

export async function createFile(projectId, { path, language, content }) {
  return apiRequest(`/projects/${projectId}/files`, {
    method: "POST",
    body: JSON.stringify({
      path,
      language,
      content,
    }),
  });
}

export async function updateFile(
  projectId,
  fileId,
  { content, language, path }
) {
  return apiRequest(`/projects/${projectId}/files/${fileId}`, {
    method: "PUT",
    body: JSON.stringify({
      content,
      language,
      path,
    }),
  });
}

export async function deleteFile(projectId, fileId) {
  return apiRequest(`/projects/${projectId}/files/${fileId}`, {
    method: "DELETE",
  });
}




