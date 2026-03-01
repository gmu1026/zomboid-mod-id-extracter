import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from './api'
import type { Job } from './api'

// ── Helpers ────────────────────────────────────────────────

function relTime(s: string): string {
  const diff = Date.now() - new Date(s.replace(' ', 'T') + 'Z').getTime()
  const m = Math.floor(diff / 60_000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function isActive(status: string) {
  return status === 'pending' || status === 'processing'
}

function stepClass(step: string) {
  const map: Record<string, string> = {
    downloading: 'p-step-downloading',
    parsing: 'p-step-parsing',
    completed: 'p-step-completed',
    cached: 'p-step-cached',
    error: 'p-step-error',
  }
  return map[step.toLowerCase()] ?? 'p-step-default'
}

// ── StatusBadge ────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

// ── CopyButton ─────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const onClick = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button className={`copy-btn${copied ? ' copied' : ''}`} onClick={onClick}>
      {copied ? 'copied' : 'copy'}
    </button>
  )
}

// ── SubmitForm ─────────────────────────────────────────────

function SubmitForm({ onSuccess }: { onSuccess: (id: string) => void }) {
  const [text, setText] = useState('')
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (ids: string[]) => api.submitJob(ids),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      setText('')
      onSuccess(job.id)
    },
  })

  const submit = () => {
    const ids = text
      .split(/[\n,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (ids.length > 0) mutation.mutate(ids)
  }

  return (
    <div className="submit-form">
      <div className="form-label">workshop ids</div>
      <textarea
        className="form-textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={'3666180085\n2392987917'}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submit()
        }}
      />
      <button
        className="form-btn"
        onClick={submit}
        disabled={mutation.isPending || !text.trim()}
      >
        {mutation.isPending ? '// submitting...' : '// extract  [ctrl+enter]'}
      </button>
      {mutation.isError && (
        <div className="form-error">{mutation.error.message}</div>
      )}
    </div>
  )
}

// ── JobsList ───────────────────────────────────────────────

function JobsList({
  selected,
  onSelect,
}: {
  selected: string | null
  onSelect: (id: string) => void
}) {
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: api.fetchJobs,
    refetchInterval: 3000,
  })

  return (
    <div className="jobs-list">
      <div className="list-header">jobs ({jobs.length})</div>

      {isLoading && (
        <div className="list-empty">loading...</div>
      )}

      {!isLoading && jobs.length === 0 && (
        <div className="list-empty">no jobs yet — submit workshop IDs above</div>
      )}

      {jobs.map((job) => (
        <div
          key={job.id}
          className={`job-item${selected === job.id ? ' active' : ''}`}
          onClick={() => onSelect(job.id)}
        >
          <div className="job-item-uuid">{job.id.slice(0, 8)}…</div>
          <div className="job-item-wids">[{job.workshop_ids.join(', ')}]</div>
          <div className="job-item-footer">
            <span className="job-item-time">{relTime(job.created_at)}</span>
            <StatusBadge status={job.status} />
          </div>
        </div>
      ))}
    </div>
  )
}

// ── ProgressLog ────────────────────────────────────────────

function ProgressLog({ progress }: { progress: api.ProgressEvent[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [progress.length])

  if (progress.length === 0) {
    return (
      <div className="progress-log">
        <div className="progress-empty">waiting for worker...</div>
      </div>
    )
  }

  return (
    <div className="progress-log">
      {progress.map((ev, i) => (
        <div key={i} className="progress-row">
          <span className={`p-step ${stepClass(ev.step)}`}>[{ev.step}]</span>
          <span className="p-msg">{ev.message}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

// ── ResultPanel ────────────────────────────────────────────

function ResultPanel({ result }: { result: api.JobResult }) {
  const { combined_config, items } = result
  const totalMods = items.reduce((n, it) => n + it.mods.length, 0)

  return (
    <>
      {/* Combined server config */}
      <div>
        <div className="section-title">server config</div>
        <div className="config-box">
          {Object.entries(combined_config).map(([key, value]) => (
            <div key={key} className="config-row">
              <div className="config-key">{key}=</div>
              <div className="config-val">
                {value ? value : <span className="config-empty">(empty)</span>}
              </div>
              {value && <CopyButton text={`${key}=${value}`} />}
            </div>
          ))}
        </div>
      </div>

      {/* Per-mod details */}
      {items.length > 0 && (
        <div>
          <div className="section-title">
            mods — {totalMods} total across {items.length} workshop item
            {items.length !== 1 ? 's' : ''}
          </div>
          {items.map((item) => (
            <div key={item.workshop_id} className="workshop-block">
              <div className="workshop-block-header">
                <span>workshop</span>
                <span className="workshop-id">{item.workshop_id}</span>
                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>
                  {item.mods.length} mod{item.mods.length !== 1 ? 's' : ''}
                </span>
              </div>
              {item.mods.map((mod) => (
                <div key={mod.mod_id} className="mod-card">
                  <div className="mod-name">{mod.name || mod.mod_id}</div>
                  <div className="mod-fields">
                    <div className="mod-field">
                      <span className="mf-key">id:</span>
                      <span className="mf-val">{mod.mod_id}</span>
                    </div>
                    {mod.mod_version && (
                      <div className="mod-field">
                        <span className="mf-key">ver:</span>
                        <span className="mf-val">{mod.mod_version}</span>
                      </div>
                    )}
                    {mod.requires.length > 0 && (
                      <div className="mod-field">
                        <span className="mf-key">requires:</span>
                        <span className="mf-val">{mod.requires.join(', ')}</span>
                      </div>
                    )}
                    {mod.maps.length > 0 && (
                      <div className="mod-field">
                        <span className="mf-key">maps:</span>
                        <span className="mf-val">{mod.maps.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

// ── JobDetail ──────────────────────────────────────────────

function JobDetail({ jobId }: { jobId: string }) {
  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.fetchJob(jobId),
    refetchInterval: (query) => {
      const data = query.state.data as Job | undefined
      return data && isActive(data.status) ? 1500 : false
    },
  })

  if (isLoading) {
    return <div style={{ padding: 20, color: 'var(--text-muted)' }}>loading...</div>
  }

  if (!job) return null

  return (
    <>
      <div className="detail-header">
        <StatusBadge status={job.status} />
        <span className="detail-id">{job.id}</span>
        <span className="detail-wids">[{job.workshop_ids.join(', ')}]</span>
        <span className="detail-time">{relTime(job.created_at)}</span>
      </div>

      <div className="detail-body">
        <div>
          <div className="section-title">
            progress ({job.progress.length} events)
          </div>
          <ProgressLog progress={job.progress} />
        </div>

        {job.error && (
          <div>
            <div className="section-title">error</div>
            <div className="error-box">{job.error}</div>
          </div>
        )}

        {job.result && <ResultPanel result={job.result} />}
      </div>
    </>
  )
}

// ── App ────────────────────────────────────────────────────

export default function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  return (
    <>
      <header className="header">
        <div className="header-pulse" />
        <div className="header-title">zme</div>
        <div className="header-sub">// zomboid mod extractor</div>
        <div className="header-spacer" />
        <div className="header-hint">ctrl+enter to submit</div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <SubmitForm onSuccess={setSelectedId} />
          <JobsList selected={selectedId} onSelect={setSelectedId} />
        </aside>

        <main className="main">
          {selectedId ? (
            <JobDetail jobId={selectedId} />
          ) : (
            <div className="empty-state">
              <div className="empty-icon">▸</div>
              <div className="empty-text">select a job to view details</div>
            </div>
          )}
        </main>
      </div>
    </>
  )
}
