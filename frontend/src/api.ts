const BASE = (import.meta.env.VITE_API_URL as string) ?? ''

export interface ProgressEvent {
  workshop_id: string
  step: string
  message: string
}

export interface ModInfo {
  mod_id: string
  name: string
  mod_version: string
  requires: string[]
  maps: string[]
}

export interface WorkshopItem {
  workshop_id: string
  mods: ModInfo[]
  server_config: Record<string, string>
}

export interface JobResult {
  items: WorkshopItem[]
  combined_config: Record<string, string>
}

export interface Job {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  workshop_ids: string[]
  progress: ProgressEvent[]
  result: JobResult | null
  error: string | null
  created_at: string
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export const fetchJobs = () => req<Job[]>('/jobs')
export const fetchJob = (id: string) => req<Job>(`/jobs/${id}`)
export const submitJob = (workshopIds: string[]) =>
  req<Job>('/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workshop_ids: workshopIds }),
  })
