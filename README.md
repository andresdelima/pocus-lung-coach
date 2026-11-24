# POCUS Lung Coach

A multi-agent AI coach that helps clinicians learn point-of-care lung ultrasound: which structures are on screen, how to move the probe, which settings to change, and a 1–10 image-quality grade, all while the scan plays as if it were live.

**Deliverables:** [`report.html`](report.html) and [`slides.html`](slides.html) open by double-clicking (screenshots embedded). Rebuild them with `.venv/bin/python scripts/build_docs.py` from `docs/*.src.html`.

> **Status:** The secure dashboard and the multi-agent coach (gpt-6-luna) work end to end on real lung clips. Without an API key, or with `POCUS_COACH_MODE=demo`, the coach runs in a clearly labeled demo mode instead.

**Scope:** lung ultrasound only, with four view cards (bat sign, intercostal A/B-lines, M-mode, PLAPS). Airway ultrasound is planned as a phase 2 project; that work is archived outside this repository.

## How the agents work

The learner taps the chest region (anterior or lateral) on a small body figure and the probe they used (linear, curvilinear or phased array), uploads an image or clip, and presses **Test**. The coach runs once and gives a verdict; it runs again only if the learner presses **Re-evaluate**.

```
region + probe + frame(s)
         ─► View Router (sees the image): picks the exact view card inside the region
frame(s) ─► Stage 1 (parallel, see the image): View & Structure Identifier · Quality Grader
         ─► Cross-check (code): if the router was unsure and the Identifier saw another view in the region, re-run once on it
         ─► Coordinator (code): safety gates, routing, landmarks scored from the Identifier's checklist
         ─► Stage 2 (parallel, text only): Probe Guidance · Settings Optimizer · Findings Tutor
         ─► Safety Checker (code): removes uncited or diagnostic statements
         ─► Coordinator: 1–10 grade computed in code, one-line coach message
```

Every agent reads the cited view card for the target view (`knowledge/view_cards/`). Prompts are in `prompts/`. Token usage and cost for every check are appended to `output/usage_log.jsonl`. To try the coach without the web app: `.venv/bin/python scripts/try_coach.py <file> <view_id>`.
>
> Educational use only. Not for diagnosis or patient care decisions.

## Run it (about 5 minutes)

Requires Python 3.12.

```bash
cd "Final Project"
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/setup_demo.py      # creates the database, encryption key and demo accounts
.venv/bin/python run.py                     # then open https://localhost:8443
```

Your browser will warn about the self-signed certificate the first time. That's expected for a local HTTPS server: choose "Advanced → Proceed". To skip HTTPS while testing, run `.venv/bin/python run.py --http` and open http://localhost:8000.

**Demo accounts (test credentials for this pilot only):**

| Role | Username | Password |
|---|---|---|
| Learner | `demo.learner` | `Learner-Demo-2026!` |
| Instructor | `demo.instructor` | `Instructor-Demo-2026!` |

**Try it:** sign in as the learner, click **Load scan**, tap *Anterior chest*, pick *Linear*, and choose a file from `data/samples/`, then press **Test**. These are synthetic images with **fake** patient details printed in the header, so you can see the de-identification work. 

**Real test clips:** `data/samples/student/` holds three short lung clips scanned by the author's students (de-identified screen recordings, metadata stripped):

| File | Tap | Probe | Head on screen | Coach result in our test |
|---|---|---|---|---|
| `student_lateral_plaps_phased.mp4` | Lateral chest | Phased array | left | PLAPS view, about 9/10 |
| `student_lateral_phased.mp4` | Lateral chest | Phased array | right | about 6/10 |
| `student_anterior_linear.mp4` | Anterior chest | Linear | left | bat-sign view, about 6/10 |

Grades can move 1–2 points between runs. To evaluate on your own labeled set instead, see the next section.

**API key:** the AI agents read `PORTKEY_API_KEY` from `.env` in this folder or in the folder above it. See `.env.example`. To call the OpenAI API directly instead of Portkey, set `POCUS_LLM_PROVIDER=openai` and `OPENAI_API_KEY`. The model is gpt-6-luna either way. The dashboard and demo mode run without a key.

## Evaluate the coach on labeled images

1. Put de-identified files in `data/pilot/images/` (optionally in subfolders named by card number, e.g. `01/`). They stay local (gitignored).
2. `.venv/bin/python scripts/make_label_sheet.py` creates `data/pilot/labels.csv` and `data/pilot/LABELING_GUIDE.md`.
3. Fill in each row: target view, chest region (`anterior` / `lateral`), probe, missing structures, your five sub-scores and 1–10 grade.
   Use `scripts/coach_blind.py <folder> --region anterior` to run the coach on unlabeled clips first, without file names.
4. `.venv/bin/python scripts/evaluate_pilot.py` (add `--repeat 2` to measure consistency). Results go to `output/eval/<run>/`: per-image `results.csv`, `summary.json` and `summary.md`.

`output/eval/smoke-reference-drawings/` is a pipeline check on the simulated reference drawings, not a clinical evaluation.

## Security and privacy

Built for data that could contain protected health information (PHI). The pilot itself uses only de-identified or synthetic images.

| Layer | What it does |
|---|---|
| Passwords | Argon2id salted hashes. Password policy: 12+ characters, 3 character types, no username. Generic error messages, constant-time check. |
| Login protection | Account lockout after 5 failures (15 min), login rate limit per IP, CSRF token on the login form |
| Sessions | Random server-side tokens (only a SHA-256 hash is stored). HttpOnly, SameSite=Strict, Secure cookies. 15-minute idle timeout, 8-hour hard limit, visible countdown. |
| Access control | Roles (learner, instructor, admin). Learners only see their own scans, and any other scan returns "not found". |
| De-identification | All metadata is removed (EXIF, video container, every DICOM header tag). The header band where scanners print name, MRN and DOB is blacked out, plus any boxes the user draws. Masking is previewed in the browser before upload and re-applied on the server. |
| Pseudonyms | Patient IDs are replaced by a keyed HMAC-SHA256 reference. The real ID is never stored. |
| Encryption at rest | Frames, metadata and coach feedback are AES-256-GCM encrypted, with a per-record binding. The key is generated on first run, has permissions 600 and is never committed. |
| Encryption in transit | HTTPS (TLS) by default |
| Application firewall | Binds to 127.0.0.1 only, IP allowlist, Host-header allowlist, per-IP rate limits, 50 MB upload cap, file-signature checks (a renamed file is rejected) |
| Browser hardening | Strict Content-Security-Policy (no inline scripts), no framing, nosniff, no-referrer, `Cache-Control: no-store` on every page |
| Audit | Every login, upload, view, coach call and deletion is logged without patient data, in a SHA-256 hash chain that exposes any edit |
| Retention | Scans are deleted automatically after 30 days. Users can delete their own scans at any time. |
| Cost control | The coach runs only when the learner presses Test. Per-user hourly cap on coach calls (300). At most 3 model requests and 45 s per agent. |

Run the tests (47 tests: security, de-identification, the evaluation math and the coordinator's safety checks, run with scripted model outputs so they cost nothing):

```bash
.venv/bin/python -m pytest -q
```

A hospital deployment would also need a vendor agreement (BAA) with the AI provider, a key-management service instead of a key file, single sign-on, and the hospital's network firewall. The app is designed around the HIPAA technical safeguards but is not, by itself, "HIPAA compliant".

## Layout

| Path | What it holds |
|---|---|
| `app/main.py` | Web app: pages and API |
| `app/security/` | Passwords, sessions, encryption, firewall, audit log |
| `app/deid.py`, `app/storage.py` | De-identification and encrypted storage |
| `app/coach/` | View-card loader, grading logic, the multi-agent coach (`agents.py`) and a demo mode |
| `app/templates/`, `app/static/` | Dashboard UI |
| `knowledge/view_cards/` | The cited teaching cards the agents use (one per view, plus the grading rubric) |
| `data/samples/` | Synthetic test files with fake identifiers |
| `scripts/` | Setup, sample generator, environment check, pilot evaluation (`evaluate_pilot.py`, `coach_blind.py`), live safety demo (`safety_demo.py`), reference images, teaching-guide PDFs, report/slides builder |
| `tests/` | Security, agent-pipeline and evaluation tests |
| `docs/` | Report and slide sources plus their images |
| `output/` | Token usage log (`usage_log.jsonl`), evaluation runs (`eval/`), safety demo |
| `Ultrasound teaching guides/` | PDF of each view card and the rubric |
| `instance/` | Runtime data: database, key, encrypted uploads, certificate (never committed) |
| `AI_prompts.md` | Log of prompts used while building |
