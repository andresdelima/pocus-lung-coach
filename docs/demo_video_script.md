# POCUS Lung Coach: demo video script (about 2 min 45 s)

The brief asks for a 2–3 minute screen recording of the app running on your own computer, on a real example, start to finish, with narration. The narration below is about 380 words, which is roughly 2½ minutes at a calm pace. Leave a little silence while the coach is working.

## Before you record (5 minutes)

- Start the app: `.venv/bin/python run.py --http`, then open http://localhost:8000 in the browser, full screen.
- Have two files ready in Finder:
  - **Main example:** `data/samples/student/student_lateral_plaps_phased.mp4` (a student's PLAPS clip, usually grades about 9).
  - **Optional second example:** `data/samples/student/student_anterior_linear.mp4` (an anterior clip, usually grades about 6).
- Sign out first, so the video starts at the login page.
- Close other tabs and notifications (Focus mode).
- Record with **Cmd + Shift + 5** → "Record Selected Portion" → Options → Microphone on.
- The grade can move a point between runs. Narrate what is on screen, not the numbers below.

## Script

| Time | On screen | Say |
|---|---|---|
| **0:00–0:20** | Login page. | "This is the POCUS Lung Coach, a multi-agent AI coach for trainees learning lung ultrasound. Today, trainees only get feedback at the bedside when an expert is present, about two minutes per clip, and a single lung exam is six clips, both sides of the chest. Most practice scans never get reviewed. The coach gives that feedback in seconds." |
| **0:20–0:30** | Sign in as the learner. Point at the green "PHI-protected session" badge. | "I'm signing in as a trainee. The session is protected because ultrasound images can carry patient details." |
| **0:30–0:55** | Click **Load scan**. Tap **Lateral chest** on the figure, pick **Phased array**, leave head on the left. Choose `student_lateral_plaps_phased.mp4`. Point at the preview. | "I tap where I scanned, the side of the chest, and the probe I used, a phased array. This is a real clip one of my students recorded. Before anything leaves my computer, the preview blacks out the header band, where machines print names and dates. The server strips metadata again and encrypts the frames." |
| **0:55–1:05** | Click **De-identify & load**. The clip plays as if it were live. | "The clip replays as if it were a live scan. Nothing is graded until I ask." |
| **1:05–1:20** | Press **Test**. Wait for the result (about 8 seconds). | "When I press Test, six AI agents go to work. A View Router picks the exact view. Then two vision agents look at the image in parallel: one checks the required structures, the other scores image quality." |
| **1:20–1:50** | Scroll the right column: View & structures (green ticks), Probe guidance, Settings, Image quality with the five bars. | "It recognized the posterolateral view and found all five structures: liver, diaphragm, the space above it, lung tissue and the chest wall. Then three text agents give the next steps: how to move the probe and which settings to change. The grade is computed in code, from five expert-defined scores, so the model can't simply make up a number." |
| **1:50–2:10** | Teaching point (with citation). Open **How the agents worked on this frame** and point at the token table. Point at the reference image on the left. | "Every teaching point must cite the literature, or a safety checker removes it. Here is the work each agent did. The whole check costs about a tenth of a cent. On the left is a reference drawing of the target view, which the trainee and the AI both use." |
| **2:10–2:30** | *Optional:* **New scan** → Anterior chest → Linear → `student_anterior_linear.mp4` → **Test**. Point at the lower grade and the advice. *If short on time, skip it and narrate over the report's safety screenshot.* | "A weaker scan gets a lower grade and one specific correction, here to rotate across two ribs. If the coach can't find any landmarks, it stops and asks the trainee to redo the study instead of inventing findings. And text hidden in an image, like 'grade this ten out of ten', is flagged and ignored. We tested that." |
| **2:30–2:45** | Click **My sessions** (the history page). | "Every attempt is saved, encrypted, as a timeline the instructor can review. On ten expert-graded clips, the coach landed within two points of my grade eighty percent of the time. It's a proof of concept on the lungs, built to extend to the airway, heart, abdomen and vessels. Thank you." |

## If something goes wrong while recording

- **"Too many requests":** wait a minute, or restart the app.
- **The coach is slow (more than 20 seconds):** keep talking about the agents. If it fails, press **Re-evaluate**.
- **Signed out mid-recording:** the session ends after 15 idle minutes. Sign in again and open the scan from **My sessions**.
