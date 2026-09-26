import { apiRequest } from "./client";

export async function listWorkspaces() {
  return apiRequest("/workspaces");
}

export async function createWorkspace({ name, description }) {
  return apiRequest("/workspaces", {
    method: "POST",
    body: JSON.stringify({
      name,
      description,
    }),
  });
}

export async function listProjects(workspaceId) {
  return apiRequest(`/workspaces/${workspaceId}/projects`);
}

export async function createProject(
  workspaceId,
  { name, description }
) {
  return apiRequest(`/workspaces/${workspaceId}/projects`, {
    method: "POST",
    body: JSON.stringify({
      name,
      description,
    }),
  });
}
