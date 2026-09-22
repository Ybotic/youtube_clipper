"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

type Clip = {
  id: number;
  title: string;
  reason: string;
  score: number;
  start: number;
  end: number;
  url: string;
};

type Job = {
  job_id: string;
  status: string;
  message: string;
  clips: Clip[];
  error?: string | null;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const stages = [
  ["downloading", "Download source"],
  ["transcribing", "Transcribe audio"],
  ["finding_moments", "Find best moments"],
  ["creating_clips", "Create verticals"],
  ["adding_captions", "Burn captions"],
];

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0")}`;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!job || ["finished", "failed"].includes(job.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`${apiUrl}/api/status/${job.job_id}`);
        if (!response.ok) throw new Error("Could not read processing status.");
        setJob(await response.json());
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Status request failed.");
      }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [job]);

  const activeStage = useMemo(() => stages.findIndex(([id]) => id === job?.status), [job?.status]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setJob(null);
    setSubmitting(true);
    try {
      const response = await fetch(`${apiUrl}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ youtube_url: url.trim() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not start this job.");
      setJob({ job_id: data.job_id, status: "queued", message: "Queued", clips: [] });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not start this job.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grain min-h-screen overflow-hidden">
      <div className="mx-auto max-w-6xl px-5 py-6 sm:px-8 sm:py-10">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-5">
          <div className="flex items-center gap-3 font-display text-sm font-bold tracking-tight">
            <span className="grid h-8 w-8 place-items-center bg-ink text-paper">A</span>
            AI CLIPPER
          </div>
          <span className="font-body text-[10px] uppercase tracking-[0.22em] text-ink/50">MVP / 001</span>
        </nav>

        <section className="grid gap-12 pb-20 pt-16 lg:grid-cols-[1fr_400px] lg:items-end lg:pt-24">
          <div>
            <p className="mb-6 font-body text-xs uppercase tracking-[0.28em] text-coral">Long form in. Short form out.</p>
            <h1 className="max-w-3xl font-display text-6xl font-bold leading-[0.91] tracking-[-0.07em] sm:text-8xl">
              Find the <span className="text-coral">moment.</span>
            </h1>
            <p className="mt-8 max-w-xl font-body text-sm leading-7 text-ink/65 sm:text-base">
              Turn long videos into ready-to-post Shorts and Reels. AI finds the story, frames it vertically, and captions every word.
            </p>
          </div>

          <form onSubmit={submit} className="relative bg-ink p-5 text-paper shadow-card sm:p-7">
            <div className="absolute right-0 top-0 h-3 w-3 bg-lime" />
            <label htmlFor="youtube-url" className="font-body text-[10px] uppercase tracking-[0.2em] text-paper/55">Source video</label>
            <input
              id="youtube-url"
              type="url"
              required
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="Paste a YouTube URL"
              className="mt-4 w-full border-b border-paper/30 bg-transparent py-3 font-body text-sm outline-none placeholder:text-paper/35 focus:border-lime"
            />
            <button disabled={submitting} className="mt-7 flex w-full items-center justify-between bg-lime px-4 py-4 font-body text-xs font-bold uppercase tracking-[0.14em] text-ink transition hover:bg-white disabled:cursor-wait disabled:opacity-60">
              {submitting ? "Starting..." : "Generate clips"}
              <span className="text-lg leading-none">-&gt;</span>
            </button>
            <p className="mt-4 font-body text-[10px] leading-5 text-paper/40">3 vertical MP4s / word-timed captions / AI selected</p>
          </form>
        </section>

        {error && <div className="mb-10 border-l-4 border-coral bg-coral/10 px-5 py-4 font-body text-xs text-ink">{error}</div>}

        {job && job.status !== "finished" && (
          <section className="mb-20 border-y border-ink/15 py-8">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <p className="font-body text-[10px] uppercase tracking-[0.2em] text-ink/45">Processing job</p>
                <h2 className="mt-2 font-display text-3xl font-bold tracking-[-0.04em]">{job.status === "failed" ? "Something went wrong" : job.message}</h2>
                {job.error && <p className="mt-2 max-w-2xl font-body text-xs leading-6 text-coral">{job.error}</p>}
              </div>
              {job.status !== "failed" && <div className="loader h-3 w-3 bg-coral" />}
            </div>
            {job.status !== "failed" && (
              <div className="mt-8 grid gap-2 sm:grid-cols-5">
                {stages.map(([id, label], index) => (
                  <div key={id} className="flex items-center gap-2 font-body text-[10px] uppercase tracking-[0.08em]">
                    <span className={`h-2 w-2 shrink-0 ${index <= activeStage ? "bg-coral" : "bg-ink/15"}`} />
                    <span className={index <= activeStage ? "text-ink" : "text-ink/35"}>{label}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {job?.status === "finished" && (
          <section className="pb-24">
            <div className="mb-8 flex items-end justify-between border-b border-ink/15 pb-5">
              <div>
                <p className="font-body text-[10px] uppercase tracking-[0.2em] text-coral">Your edit is ready</p>
                <h2 className="mt-2 font-display text-4xl font-bold tracking-[-0.05em]">Three moments worth posting.</h2>
              </div>
              <span className="hidden font-body text-xs text-ink/45 sm:block">1080 x 1920 / MP4</span>
            </div>
            <div className="grid gap-8 md:grid-cols-3">
              {job.clips.map((clip) => (
                <article key={clip.id} className="group">
                  <div className="relative overflow-hidden bg-ink shadow-card">
                    <video controls playsInline preload="metadata" className="aspect-[9/16] w-full object-cover" src={`${apiUrl}${clip.url}`} />
                    <span className="absolute left-3 top-3 bg-lime px-2 py-1 font-body text-[10px] font-bold text-ink">{clip.score}/100</span>
                  </div>
                  <div className="pt-5">
                    <div className="flex items-start justify-between gap-4">
                      <h3 className="font-display text-xl font-bold leading-tight tracking-[-0.03em]">{clip.title}</h3>
                      <span className="shrink-0 font-body text-[10px] text-ink/45">{formatTime(clip.start)}</span>
                    </div>
                    <p className="mt-3 min-h-12 font-body text-xs leading-5 text-ink/55">{clip.reason}</p>
                    <a href={`${apiUrl}${clip.url}`} download={`clip_${clip.id}.mp4`} className="mt-5 inline-flex border-b-2 border-ink pb-1 font-body text-[10px] font-bold uppercase tracking-[0.14em] transition hover:border-coral hover:text-coral">Download MP4 -&gt;</a>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        <footer className="flex justify-between border-t border-ink/15 py-5 font-body text-[10px] uppercase tracking-[0.15em] text-ink/40">
          <span>AI-assisted editing</span>
          <span>Built for the scroll</span>
        </footer>
      </div>
    </main>
  );
}
