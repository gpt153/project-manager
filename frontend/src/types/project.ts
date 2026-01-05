export interface ProjectColor {
  primary: string;
  light: string;
  veryLight: string;
  text: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  github_repo_url?: string;
  telegram_chat_id?: number;
  created_at: string;
  updated_at: string;
  open_issues_count?: number;
  closed_issues_count?: number;
  color?: ProjectColor; // Generated client-side
}

export enum ProjectStatus {
  BRAINSTORMING = 'BRAINSTORMING',
  VISION_REVIEW = 'VISION_REVIEW',
  PLANNING = 'PLANNING',
  IN_PROGRESS = 'IN_PROGRESS',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
}

export interface Issue {
  number: number;
  title: string;
  state: 'open' | 'closed';
  created_at: string;
}

export interface Document {
  id: string;
  name: string;
  type: 'vision' | 'plan' | 'other';
  url: string;
}
