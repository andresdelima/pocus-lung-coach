# AI Prompts Log

This file logs what I typed during vibe coding for the final project.

## Setup: Project Context

### Prompts Typed

> Today we are going to be working on the final project for my class. Prepare folders and necessary environments to start working on this

> Yes, the general briefing is in this website: https://zlisto.github.io/mgt_409_fa26/project_requirements.html
> Study it in detail. Let me know if you have any questions.

> Answers:
> 1. Yes, we will have a real user.
> 2. Local is ok
> 3. You can keep AI prompts to keep track of what we do
> 4. Yes, that sounds good so the slides can be accessed offline

## Step 1: Project Idea and Design

### Prompts Typed

> Ultrasound is an important tool used in medicine to help evaluate patients and diagnose conditions in real time. [...] My goal is to create an AI agent that is able to assist in real time image acquisition and interpretation. [...] identify the structures that are being seen, give feedback in terms of the way the ultrasound probe is being positioned and also recommend setting adjustments for image generation optimization. Ultimately I would want the agent to be able to grade the images using some type of ordinal scale (ie. 1-10).
>
> For this experimental model, we will focus only on the respiratory system [...]
>
> I think we could have one boss who delegates tasks and other agents who are in charge of: 1. structure identification, 2. provide guidance as to how to reorient to improve image, 3. optimize settings for better image quality, 4. grade image obtained, 5. etc (suggest any other function you may consider adequate).
>
> [...] I would like to have users log in through a portal that requires username and password (hashed for safety)
>
> Do not run anything yet. Think about the request and how we would structure this to work nicely. Then propose a step by step sequence on how to execute this project.

### Follow-Up Prompt

> 1. Since this is a pilot, we will work with the upload mode in which I will upload still images or short clips.
> 2. I will be uploading either a short clips or images of M mode.
> 3. Understood
> 4. Pilot data is clear of any identifiers. However, the model we build should incorporate mechanisms that simulate interacting with data that may have patient identifiers and is able to clear those or keep them in a secure fashion. Implement some encrypting or hashing as we've done in other activities in this course.

What was lacking: the first design assumed live scanning and real patient data; this narrowed it to uploads and added a simulated-identifier privacy layer.

### Second Follow-Up Prompt

> [...] we will be working with upload mode, meaning since this is just a pilot, I will be supplying short clips and images, but the dashboard that we built for the model should pretend that this is real-time images. [...] We will test Luna with basic images first, and then move on to higher complexity things like video [...] the assignment asks me to create a model that would be able to work with real life ultrasound. In that case, I would want you to create a dashboard that has all the security features, including hashing, firewalls, encrypting, and other necessary security features to provide adequate protection of PHI.

What was lacking: the design did not yet say the dashboard should look live, the order of model tests (stills before video), or the full set of PHI security controls.

## Step 2: Knowledge Base

### Prompts Typed

> I am going to provide you with some educational content that I have developed in the past . Please make sure you use some of this information to train the agents that are going to be providing feedback and education. I will also provide academic literature .

> Here are papers on lung ultrasound. Use this to train your agents
> (Shared folder: Literatura/Critical Care articles/Lung Ultrasound, 6 PDFs)

> I'll review them
> (view cards and grading rubric)

> Here are the papers on upper airway ultrasound
> (Shared 4 PDFs from Literatura/Critical Care articles/Lung Ultrasound/Airway)

## Step 3: Learner Dashboard

### Prompts Typed

> ok lets start generating the dashboard for learners

## Step 4: AI Agents

### Prompts Typed

> Build the agents

> Review cards first
> (author reviewing the view cards before sharing pilot images; a review checklist was added at knowledge/REVIEW_CHECKLIST.md)

## Step 5: Extra Teaching Resource

### Prompts Typed

> I found a really good resource on lung ultrasound teaching. Please review it carefully and incorporate elements here to the cards that we are creating to train our AI agents:
> https://www.pocus101.com/lung-ultrasound-made-easy-step-by-step-guide/

## Step 6: More Airway Resources and Intellectual-Property Screen

### Prompts Typed

> I found a few more resources for the airway ultrasound. Incorporate to the training cards.
>
> In general, for all the resources that we have used, since we may not have adequate copyright, go ahead and screen everything to make sure we do not include any propietary data. Concepts should be paraphrased and images/videos/pictures and schematics should only be use for internal training of our model. None of these should be up in our portal given intellectual property concerns. We do not want to use intellectual property without explicit authorization unless it is open to the public. Make sense? If any doubts, ask me directly, do not make assumptions.

### Follow-Up Prompt

> (Shared Lin 2023 "Point-of-Care Ultrasound in Airway Evaluation and Management" PDF and) https://asra.com/news-publications/asra-newsletter/newsletter-item/asra-news/2021/08/02/pocus-spotlight-airway

What was lacking: the first message didn't name the resources, so only the one new PDF in the Airway folder was found; this named both.

> remove Flower, never send figures, keep coach focused on acquisition

## Step 7: Card-by-Card Review with the Author

### Prompts Typed

> ok lets do it
> (chose "Review cards together": one card at a time, airway cards first)

Card 06 answers:

> 1. ok 2. No rule of thumb, rely on images. We can adjust these as we go and test the model further. 3. yes, by convention we can say towards marker and marker towards head (cephalad) 4. All 4 structures are the minimum. Others like major blood vessels (carotid artery, internal and external jugural vein) may be important to identify on longitudinal views (lateral). 5. Remove procedures. Maybe just mention that idenfying the CTM is important as this is the site for a crycothyroidotomy. 6. Not right now. I would like to review all cards before approving after we go over these cheklists for each card.

Card 07 answers:

> 1. yes 2. ok 3. yes 4. agree 5. enough

Card 08 answers and a new resource:

> 1. yes 2. yes 3. all are good 4. keep it concise. Agreed with the supplementing the capnography and auscultation. Also can add evaluating lung sliding (bilateral) to ensure adequate aeration of lung fields. 5. good
>
> Here is an additional resource: https://www.aliem.com/pem-pocus-series-confirmation-endotracheal-tube/ same copyright rules as before.
>
> Also, if the patient has a breathing tube, it is hard for them follow instructions. So get rid of the part that says "ask the patient to swallow" etc

Card 09 answers:

> 1. yes 2. ok 3. yes 4. keep 5. trim

Card 10 answers:

> 1. keep 2. yes 3. yes 4. ok 5. trim

Card 01 answers:

> 1. yes 2. ok 3. agree 4. trim 5. keep

Card 02 answers:

> 1. agreed 2. ok. include cues to differentiate b lines from z lines 3. yes 4. agreed 5. 6 point is simple and better for this case. Go with this

Card 03 answers:

> 1. ok 2. yes 3. agreed 4. yes

Card 04 answers:

> 1. yes 2. ok 3. yes, add lung tissue too 4. agreed 5. yes

Card 05:

> get rid of this card

Grading rubric answers:

> 1. Landmarks are fundamental for a beginner, give this more weight. We need to make sure the learner is looking at the right thing. Then we can work on fine tunning and details. 2. ok 3. ok 4. ok

What was lacking: the cards were drafted from the literature alone, so they had no probe-marker convention, no depth values, and clinical statistics and procedure steps that went beyond an acquisition coach. The author's answers set the convention (marker to the head or to the patient's right), approved starting depths, trimmed the scope to image findings, removed the diaphragm card, and weighted landmarks double in the grade.

## Step 8: Simulated Reference Image for Each Card

### Prompts Typed

> 1. keep 2. trim 3. keep
>
> Can you reorganize the cards in ascending order (1 to 9)

> how can I open the cards?

> for each card, create a fake image that resembles the "ideal" ultrasound view, so the agent and trainee has a reference point

### Follow-Up Prompt

> (Answered two questions: send the reference images to the model as well as to the trainee, which updates the IP rule; style "simulated + labeled".)

What was lacking: the request didn't say whether the model should also see the images, and the IP rule said model example images could come only from the author's pilot images. Asking settled both.

> Review the images first

> (Pasted a new OpenAI API key — not reproduced here.) gpt-6-luna only

What was lacking: the Portkey key had stopped working. The new key is a direct OpenAI key, so the app gained a `POCUS_LLM_PROVIDER=openai` option; Portkey stays the default, and the model stays gpt-6-luna.

## Step 9: Pilot Evaluation Kit

### Prompts Typed

> all OK. I'll review them again later before we finalize the whole thing. Remind me to do so.
>
> Anything else needed now? or can we move forward?

> Yes, build it

## Step 10: Body-Region Picker, Probe Picker and On-Demand Grading

### Prompts Typed

> show me the dashboard for now

> how to I log in?

> link is broken

> Lets make a few changes:
>
> 1. for the target view: theres only two options that we are analyzing with this demo a. airway b. lungs. Substitute the drop down menu for a more interactive small character that the user can click to identify the part of the body that they are scanning.
> 2. to assist with an easier identification of the image profile and location, create a selection option (graphic, no drop down) in which the user can tell you which probe is being used; 3 options - curvilinear, linear and phased-array
> 3. the grading should not be on a cycling basis (ie time based). Once the user uploads the image/clip and hits test, then run your test and give a veridic. No re-evaluation unless the user requests to re-evaluate

What was lacking: with only a body region chosen, the coach still needs one exact view card to grade against. A View Router agent was added to pick it, plus a cross-check against the Identifier when the router is unsure.

## Step 11: First Pilot Clips

### Prompts Typed

> Add pilot images

> there is a folder named pilot images inside ultrasound images folder within the final project folder. find it and upload the clips. there is only 3 so far

> for these 3 images, the right side of the screen is cephalad

What was lacking: the cards assume the head is on the left of the screen. Uploads now record which side the head is on, and the agents are told, so a mirrored image isn't penalized and directions say "toward the head" instead of screen left/right.

## Step 12: PDF Teaching Guides

### Prompts Typed

> Show me the grading matrix before I can produce an objective grade

> 1: 01 - none - 2+2/2/2/2/2 -> 12/12: grade 10

> I need to see the cards. Can you create a new folder within the final assignment folder named "Ultrasound teaching guides". In it, put each of these in the form a pdf that it is easy accessible and interpretable to a human. Make sure you include the images/graphics we created for demonstration purposes

## Step 13: Landmark Gate

### Prompts Typed

> One more change to workflow: if the landmark score is 0, then the process should be stopped. The learner should be advancing with further interpretation or fine tunning of their image if the initial landmark acquisition is not there, so this would need to be addressed.

## Step 14: Pilot Grading and First Evaluation

### Prompts Typed

> continue grading pilot images:
>
> 3. anterior chest: 2+2/2/1/2/2 --> 11/12. Score = 9

> Yes, apply both

What was lacking: the first evaluation showed the coach grading 3.5 points stricter than the author. It was anchoring on the clean reference drawing, and its depth rule was stricter than the author's practice. Both were fixed; the error dropped to 1.5 points (see output/eval/calibration_2026-11-23.md).

> I want to make a change to our process: landmarks should be worth 2 points again (as in the begining). However, a score of at least 1 MUST be obtained to be allowed to continue. A zero in landmarks means study is uninterpretable as we had previously discussed and so the study needs to be redone by the learner

> what is the usernae and pw again?

> Lets grade clip 2

> I just noticed the picture for the reference card for the PLAPS is off: liver should be UNDER the diaphragm. Diaphragm is concave over liver. Adjust echogenicity too please

> 2: PLAPS - 2/2/2/2/2 --> 10/10

> Yes, full credit

What was lacking: with all 3 clips labeled, the coach under-scored orientation on 5 of 6 checks. The clips show the head on the right of the screen, and the author decided that a mirrored display deserves full credit. The rule was made explicit in the grader prompt and the rubric. A second gap turned up: the Grader saw only one frame of each clip and marked interpretability down for "no motion"; it is now told the frame comes from a clip. Landmarks now match the author 100% of the time; orientation (oblique/off-center) and gain/focus remain 1 point strict each.

> Yes, loosen both

What was lacking: the coach still took a point for a slightly oblique target and for normal speckle. A leeway rule was added to the grader prompt and rubric. The error fell from 2.2 to 1.2 points; orientation remains the main gap.

> Yes, if the beam is fine

What was lacking: the coach treated a pleural line or diaphragm that slants on screen as an orientation error. Orientation is now judged by the beam angle (a bright, sharp target), not by whether the line is horizontal. The error fell to 1.0 point and the bias to −0.33.

> ok I addded a bunch of new ones inside a folder called "test lung". Find them and test them. Do not use the name of the file to distinguish any characteristics of the actual clip. Only graphical cues.

> L01: 01 Anterior pleura - 1/1/1/2/2 --> 7 … L07: 04 - PLAPS - 2/2/1/2/2 --> 10

> 1. yes 2. 9 / Take from the name

What was lacking: the author's grades followed the folder order, not the blind names, so the mapping had to be confirmed, and the PLAPS sum was corrected from 10 to 9. On 10 clips, the coach grades 2.3 points below the author, mostly on interpretability, gain and depth with a curvilinear probe.

> Yes, apply all three

What was lacking: the coach lowered interpretability when it was itself unsure of the finding, marked down normal deep-field speckle, and applied linear-probe depth to a curvilinear clip. After the fixes the error fell from 2.6 to 1.75 points and repeat consistency rose from 40% to 70%; M-mode and the curvilinear B-line clip remain the weak spots.

> Tune M-mode first

What was lacking: the M-mode frames were shrunk to 800 px, which left the small B-mode inset unreadable, and the grader expected to see a breath and a textbook bat sign. The coach now sends only the latest trace frame at 1280 px, with M-mode grading rules. M-mode error fell from 3.0 to 2.0 points and the overall error to 1.55, but repeat consistency dropped.

> Steady the stop rule

What was lacking: one noisy checklist call could stop a study the learner had acquired (L06 was stopped on one run and graded 6 on the other). The stop now needs a second opinion from the Grader or a wrong-view call. The error fell to 1.40 points and rank agreement with the author rose to 0.63.

> Ok since the deadline is so close and it has taken so much to fine tune the agents grading, this prove of concept should only focus on lung ultrasound. We are going to save the airway piece for a second phase (separate project). Before we move forward with deliverables, lets remove everthing on airway evaluation, as this model is only going to focus on lung ultrasound. That means that the trainees still get to pick the probe that they are using (1 of 3) and for the little dummy pick anterior vs lateral, as this will help our agents understand the picture being evaluated.
>
> I do want you to save all the work on airway US, as I want to use this on a second phase of this project later.

What was lacking: the scope was too wide for the deadline. The whole project was snapshotted to `AI Foundations/POCUS Phase 2 - Airway (archive)/`; airway cards, images, PDFs, code paths and tests were removed; the body figure now offers anterior vs lateral chest. A rib-shadow tie-breaker was added to the View Router after two anterior clips were routed to the intercostal card.

> Lets have the platform test some student models first
> I would like to upload using the actual portal... remind me the student login
> I uploaded a few, looks good! I think we can move forward with the deliverables

What was lacking: the report needed real evidence. A live prompt-injection test on a real frame (`scripts/safety_demo.py`), portal screenshots, token statistics from 137 real checks, and the author's answers on current practice (bedside feedback only, about 2 min per clip) were gathered. Opening a clip twice tripped the per-IP rate limit (each clip loads ~120 frames), so frame reads got their own bucket. `report.html` and `slides.html` are built from `docs/*.src.html` by `scripts/build_docs.py`; a fresh-copy test with `.env` one folder up passed (install 31 s, 47 tests, real model call).

> Name is ok
>
> For the real user evidence, can you show screenshots of the previous sessions analyzing the "student" clips?
>
> For test data, include the last 3 clips that I uploaded (student files). If more are needed, I can provide more
>
> Take the draft markers off, I have verified these
>
> Lastly, merge all the forks in this session.

What was lacking: the report showed only one student session. The four student sessions were captured from the portal and added. The last uploads were matched to their source files by comparing stored frames; three distinct clips were re-encoded without metadata into `data/samples/student/`. The cards and rubric are now marked approved by the author. The forks share one folder with no branches, so there was nothing to merge.
