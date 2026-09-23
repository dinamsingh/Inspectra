/**
 * Single source of truth for identity, links, and status.
 * Nothing outside this file should hardcode a resource URL or the prototype status.
 */

export type PrototypeStatus =
  | 'in-development' // actively built, no public build to open yet
  | 'preview-available' // an unstable build exists at PROTOTYPE_URL
  | 'live' // stable, publicly usable

export interface ProjectConfig {
  PROJECT_NAME: string
  PROJECT_ID: string
  TEAM_NAME: string
  GITHUB_URL: string
  PROTOTYPE_URL: string | null
  PROTOTYPE_STATUS: PrototypeStatus
  DEMO_VIDEO_URL: string | null
}

export const projectConfig: ProjectConfig = {
  PROJECT_NAME: 'Inspectra',
  PROJECT_ID: 'SIH26034',
  TEAM_NAME: '',
  GITHUB_URL: 'https://github.com/dinamsingh/Inspectra',
  PROTOTYPE_URL: null,
  PROTOTYPE_STATUS: 'in-development',
  DEMO_VIDEO_URL: null,
}
