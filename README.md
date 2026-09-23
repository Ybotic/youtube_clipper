# AI Clipper

AI Clipper turns a YouTube video into three ready-to-post vertical Shorts/Reels. It downloads the source, transcribes speech with Whisper, asks an OpenAI model to find the strongest moments, then renders 9:16 MP4s with word-timed captions.

## Architecture

```text
frontend/                 Next.js + TypeScript + Tailwind UI
backend/main.py           FastAPI API and in-memory job state
backend/pipeline.py       Pipeline orchestration only
backend/services/
  downloader.py            YouTube acquisition and URL validation
  transcription.py         Whisper word-level transcript JSON
  clip_detector.py         Structured OpenAI clip selection
  captions.py              ASS caption generation
  video_editor.py          FFmpeg crop, encode, and caption burn-in
temp/                      Per-job source/transcript scratch files
output/                    Completed job MP4s
```

The API has three useful endpoints:

- `POST /api/generate` with `{ "youtube_url": "..." }`
- `GET /api/status/{job_id}` for processing state and finished clip metadata
- `GET /api/clips/{job_id}/clip_1.mp4` for a rendered file

Jobs are intentionally in memory for this MVP. A process restart clears active jobs.

## Prerequisites

- Python 3.11 (recommended; the included Dockerfile uses 3.11)
- Node.js 18.17 or newer and npm
- FFmpeg available on `PATH`, including the `subtitles` filter
- An OpenRouter API key
- A machine with enough disk space for downloaded videos and enough memory for Whisper

Install FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg
```

`openai-whisper` also relies on the FFmpeg executable to read video audio.

## Local Setup

From the project root:

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY in .env

# Python 3.11 is recommended. uv can install it without system sudo access.
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu torch
uv pip install --python .venv/bin/python setuptools==69.5.1 wheel==0.45.1
uv pip install --python .venv/bin/python --no-build-isolation -r backend/requirements.txt
source .venv/bin/activate

cd frontend
npm install
```

If FFmpeg is not installed system-wide, set `FFMPEG_BINARY` to its absolute path
in `.env`. The application also auto-detects `./.tools/bin/ffmpeg`.

Run the backend in one terminal:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Run the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000), paste a YouTube URL, and select **Generate clips**.

The first Whisper run downloads the configured model. `WHISPER_MODEL=base` is a reasonable local MVP default; `small`, `medium`, or `turbo` can improve accuracy at a higher compute cost.

## Docker

Docker is useful when you want the FFmpeg dependency packaged with the backend. Create `.env` first, then run:

```bash
```

The frontend is at `http://localhost:3000` and the API is at `http://localhost:8000`. Whisper and PyTorch can make the backend image large and may require additional memory.

## Processing Pipeline

1. The API validates the URL and creates an in-memory job.
2. `yt-dlp` downloads one video into the job's temporary directory.
3. Whisper extracts segments and word timestamps into `transcript.json`.
4. OpenAI receives the timestamped transcript and returns five structured candidates. The service removes invalid or overlapping candidates and keeps the top three.
5. FFmpeg seeks to each time range, center-crops to 1080x1920, and encodes H.264/AAC MP4.
6. The caption service maps transcript words into short ASS events. FFmpeg burns those events into each final MP4.
7. Status returns clip titles, scores, explanations, timestamps, and download URLs.

## Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Required for clip selection | none |
| `OPENROUTER_MODEL` | OpenRouter model for clip selection | `openai/gpt-5.6-luna` |
| `WHISPER_MODEL` | Whisper model name | `base` |
| `MAX_VIDEO_SECONDS` | Download duration limit | `7200` |
| `FRONTEND_ORIGIN` | Allowed browser origin | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Frontend API origin | `http://localhost:8000` |
| `FFMPEG_BINARY` | Optional FFmpeg executable path | auto-detected local binary or `ffmpeg` |

## Known Limitations

- There is no authentication, persistent database, queue, or cloud storage.
- Processing happens on the backend process, so only a small number of local jobs should run at once.
- Vertical framing is a center crop; it does not track faces or speakers.
- Caption emphasis is grouped word-timed text rather than per-word karaoke highlighting.
- Whisper and FFmpeg must be installed and available to the process/container.
- Some videos may be unavailable because of region, age, login, or YouTube download restrictions.

## Future Improvements

Face tracking, speaker detection, alternate caption styles, hooks/B-roll, automatic zooms, background blur, additional aspect ratios, direct publishing, accounts, saved projects, cloud workers, queues, analytics, and performance-based clip learning can be added behind the isolated services later.
