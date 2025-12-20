import { Project, Document } from '@/types/project';

const API_BASE_URL = '/api';

export const api = {
  // Projects
  getProjects: async (): Promise<Project[]> => {
    const response = await fetch(`${API_BASE_URL}/projects`);
    if (!response.ok) throw new Error('Failed to fetch projects');
    return response.json();
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
    if (!response.ok) throw new Error('Failed to fetch project');
    return response.json();
  },

  createProject: async (name: string, description?: string): Promise<Project> => {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    if (!response.ok) throw new Error('Failed to create project');
    return response.json();
  },

  // Documents
  getVisionDocument: async (projectId: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/documents/vision/${projectId}`);
    if (!response.ok) throw new Error('Failed to fetch vision document');
    return response.text();
  },

  listDocuments: async (projectId: string): Promise<Document[]> => {
    const response = await fetch(`${API_BASE_URL}/documents/list/${projectId}`);
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
  },
};
