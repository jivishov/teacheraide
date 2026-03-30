# TeacherAide

**AI-powered assessment generator for educators.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-teacheraide.fly.dev-blue)](https://teacheraide.fly.dev)

TeacherAide lets teachers upload PDF reading materials or images, then uses AI to generate standards-aligned assessment questions in seven formats. Generated questions are exported as QTI 2.2 packages (importable into any LMS) or Word documents, and can be published directly to students via the built-in student platform.

---

## Features

### Question Types
| Type | Description |
|---|---|
| MCQ | Multiple Choice (single correct answer) |
| MRQ | Multiple Response (one or more correct answers) |
| True/False | Binary choice |
| Fill-in-the-Blank | Cloze-style text completion |
| Matching | Match items across two columns |
| Ordering | Arrange items in correct sequence |
| Essay | Extended written response |

### AI Providers & Models

**OpenAI**
- gpt-5.4 _(default for text questions)_
- gpt-5.2, gpt-5.1, gpt-5-mini
- o4-mini, o3-mini, o1, o1-mini _(reasoning models)_

**Anthropic (Claude)**
- claude-opus-4-6 _(default for image questions)_
- claude-sonnet-4-6, claude-haiku-4-5

**Google Gemini**
- gemini-3.1-pro-preview _(default)_
- gemini-3-pro-image-preview, gemini-3.1-flash-image-preview _(with image generation)_
- gemini-3-flash-preview

Each provider supports extended thinking / reasoning modes with configurable budgets.

### Assessment Presets
| Preset | MCQ | MRQ | T/F | FIB | Order | Match | Essay |
|---|---|---|---|---|---|---|---|
| Formative | 4 | 1 | 2 | 2 | 0 | 0 | 1 |
| Summative | 6 | 2 | 2 | 2 | 1 | 1 | 2 |
| Quick-Check | 4 | 0 | 3 | 1 | 0 | 0 | 0 |
| Homework | 5 | 1 | 2 | 2 | 1 | 1 | 1 |

Question counts are fully customizable per type (0–20).

### Other Highlights
- **Dual workflow** — generate new questions from content, or extract existing questions from PDFs
- **Image questions** — up to 10 images per session (PNG, JPEG, GIF, WebP)
- **QTI 2.2 export** — ZIP packages importable into Canvas, Blackboard, Moodle, etc.
- **Word export** — printable question sets
- **Real-time progress** — live status through Validating → Generating → Packaging stages
- **Secure key storage** — API keys stored in OS keyring (Windows Credential Manager / macOS Keychain)
- **Student platform** — publish assessments, manage sections, and score responses

---

## Tech Stack

- **[Reflex](https://reflex.dev)** — Python full-stack web framework (backend + compiled React frontend)
- **Tailwind CSS v3** — utility-first styling
- **OpenAI / Anthropic / Google Gemini SDKs** — multi-provider LLM access
- **SQLAlchemy + SQLite** _(in progress)_
- **Docker + Nginx + Supervisord** — containerized deployment
- **[Fly.io](https://fly.io)** — production hosting (region: `dfw`)

---

## Project Structure

```
app/
├── app.py              # Route registration (entry point)
├── pages/              # One file per route (landing, upload, text-questions, image-questions, review, settings, student-platform, reading-material)
├── states/             # Reflex state classes (business logic + reactive state)
├── components/         # Reusable UI building blocks
├── utils/              # LLM handlers, QTI/YAML conversion, file I/O, model catalog
└── prompts/            # LLM prompt templates per question type
```

---

## Quick Start

**Prerequisites:** Python 3.12+, at least one LLM API key.

```bash
git clone https://github.com/jivishov/teacheraide.git
cd teacheraide
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
reflex run                 # Windows: run.bat
```

Open `http://localhost:3000`. Enter API keys on the **Settings** page (or set env vars — see below).

---

## Deployment (Fly.io)

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
fly auth login
fly deploy

# Set API keys as secrets (never bake into the image)
fly secrets set \
  OPENAI_API_KEY=sk-... \
  CLAUDE_API_KEY=sk-ant-... \
  GEMINI_API_KEY=AIza...
```

The container runs three processes under Supervisord:

| Process | Port | Role |
|---|---|---|
| Reflex backend | 8000 | API + WebSocket (`/_event`) |
| Reflex frontend | 3000 | Compiled React app |
| Nginx | 80 | Reverse proxy (public entry point) |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | One of three required | OpenAI API key |
| `CLAUDE_API_KEY` | One of three required | Anthropic API key |
| `GEMINI_API_KEY` | One of three required | Google Gemini API key |
| `OPENAI_REASON_MODEL` | No | Override default reasoning model |
| `API_URL` | Yes (prod) | Public URL the browser connects to, e.g. `https://teacheraide.fly.dev` |
| `TEACHERAIDE_DATABASE_URL` | No | SQLite path or PostgreSQL URL (default: `sqlite:////app/data/teacheraide.db`) |
| `TEACHERAIDE_MEDIA_ROOT` | No | Path for uploaded media (default: `/app/data/platform_media`) |

---

## Workflow

```
1. Upload Material     →  PDF document or images
2. Configure           →  Choose preset, question types, AI model
3. Generate            →  AI produces questions (with live progress)
4. Review & Export     →  Edit questions, download QTI ZIP or Word doc
                          (optional) Publish to student platform
```

---

## License

MIT
