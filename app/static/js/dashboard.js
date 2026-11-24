// Learner dashboard: upload with de-identification preview, simulated live playback, and the coach panel.
(function () {
  const cfg = JSON.parse(document.getElementById("page-config").textContent);
  const $ = (id) => document.getElementById(id);
  const el = {
    img: $("frame-img"), empty: $("screen-empty"), live: $("live-badge"), monView: $("mon-view"),
    monFrame: $("mon-frame"), play: $("btn-play"), step: $("btn-step"), scrub: $("scrub"),
    analyze: $("btn-analyze"),
    gradeBadge: $("grade-badge"), timeline: $("timeline"), notice: $("coach-notice"),
    viewTarget: $("view-target"), structures: $("structures"), probe: $("probe"), settings: $("settings"),
    gradeBig: $("grade-big"), gradeBand: $("grade-band"), subscores: $("subscores"), teaching: $("teaching"),
    privacy: $("privacy"), usage: $("usage"), headline: $("headline"), flags: $("flags"),
    observations: $("observations"), routing: $("routing"), agentTable: $("agent-table"),
    dialog: $("upload-dialog"), form: $("upload-form"), file: $("file"), probeHint: $("probe-hint"),
    patient: $("patient-id"), mask: $("mask-pct"), maskVal: $("mask-val"), canvas: $("preview"),
    previewNote: $("preview-note"), uploadErr: $("upload-error"), confirm: $("confirm-upload"),
    refCard: $("ref-card"), refImg: $("ref-img"), refLabels: $("ref-labels"),
  };

  // Simulated reference drawing for the view being coached (app/static/reference, made by
  // scripts/make_reference_images.py). With a body region, it appears once the View Router has chosen the view.
  function showReference(viewId) {
    if (viewId !== undefined) state.refView = viewId;
    const v = state.refView;
    if (!v || !cfg.views[v]) { el.refCard.hidden = true; return; }
    el.refImg.src = `/static/reference/${encodeURIComponent(v)}${el.refLabels.checked ? "_labeled" : ""}.png?v=${cfg.v}`;
    el.refCard.hidden = false;
  }
  el.refLabels.addEventListener("change", () => showReference());
  el.refImg.addEventListener("error", () => { el.refCard.hidden = true; });

  const state = { scan: null, frames: [], idx: 0, playing: false, playTimer: null,
                  inflight: false, feedback: [], viewName: "", refView: null, region: "", probe: "", head: "left" };

  // ---------------- body-region figure and probe picker ----------------
  const TYPICAL = { anterior: ["linear"], lateral: ["curvilinear", "phased_array"] };
  function pickRegion(r) {
    state.region = r;
    document.querySelectorAll("[data-region]").forEach((n) => {
      const on = n.dataset.region === r;
      n.classList.toggle("selected", on);
      if (n.getAttribute("role") === "radio") n.setAttribute("aria-checked", on);
    });
    document.querySelectorAll(".probe-opt").forEach((b) =>
      b.classList.toggle("typical", !!r && TYPICAL[r].includes(b.dataset.probe)));
    el.probeHint.textContent = r ? `Usually ${TYPICAL[r].map((x) => cfg.probes[x].toLowerCase()).join(" or ")} for this region` : "";
  }
  function pickProbe(pr) {
    state.probe = pr;
    document.querySelectorAll(".probe-opt").forEach((b) => {
      b.classList.toggle("selected", b.dataset.probe === pr); b.setAttribute("aria-checked", b.dataset.probe === pr);
    });
  }
  document.querySelectorAll("[data-region]").forEach((n) => {
    n.addEventListener("click", () => pickRegion(n.dataset.region));
    n.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pickRegion(n.dataset.region); } });
  });
  document.querySelectorAll(".probe-opt").forEach((b) => b.addEventListener("click", () => pickProbe(b.dataset.probe)));
  function pickHead(h) {
    state.head = h;
    document.querySelectorAll(".head-opt").forEach((b) => {
      b.classList.toggle("selected", b.dataset.head === h); b.setAttribute("aria-checked", b.dataset.head === h);
    });
  }
  document.querySelectorAll(".head-opt").forEach((b) => b.addEventListener("click", () => pickHead(b.dataset.head)));
  const probeName = (p) => (p && cfg.probes[p]) || "not given";

  // ---------------- helpers ----------------
  const gradeClass = (g) => (g == null ? "ungraded" : g <= 3 ? "g-bad" : g <= 6 ? "g-mid" : "g-good");
  function li(html, cls) { const x = document.createElement("li"); if (cls) x.className = cls; x.innerHTML = html; return x; }
  function esc(s) { return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

  // ---------------- upload dialog ----------------
  let previewSource = null;   // HTMLImageElement or HTMLVideoElement
  let boxes = [];             // redaction boxes in fractions of width/height
  let drag = null;

  function openUpload() {
    el.form.reset(); boxes = []; previewSource = null; el.uploadErr.textContent = "";
    pickRegion(""); pickProbe(""); pickHead("left");
    el.maskVal.textContent = `${cfg.defaultMask}%`; drawPreview();
    el.previewNote.textContent = "Preview appears here. Nothing is uploaded until you confirm.";
    el.dialog.showModal();
  }
  $("open-upload").addEventListener("click", openUpload);
  $("btn-new").addEventListener("click", openUpload);
  $("cancel-upload").addEventListener("click", () => el.dialog.close());
  $("clear-boxes").addEventListener("click", () => { boxes = []; drawPreview(); });
  el.mask.addEventListener("input", () => { el.maskVal.textContent = `${el.mask.value}%`; drawPreview(); });

  el.file.addEventListener("change", () => {
    const f = el.file.files[0];
    previewSource = null; drawPreview();
    if (!f) return;
    const ext = f.name.toLowerCase().split(".").pop();
    const url = URL.createObjectURL(f);   // stays in this browser; nothing is sent yet
    if (["png", "jpg", "jpeg"].includes(ext)) {
      const im = new Image(); im.onload = () => { previewSource = im; drawPreview(); }; im.src = url;
      el.previewNote.textContent = "Black areas will be removed before upload. Drag to add more boxes.";
    } else if (["mp4", "mov", "m4v", "avi"].includes(ext)) {
      const v = document.createElement("video"); v.muted = true; v.src = url; v.preload = "auto";
      v.addEventListener("loadeddata", () => { v.currentTime = Math.min(0.2, v.duration / 2 || 0); });
      v.addEventListener("seeked", () => { previewSource = v; drawPreview(); });
      el.previewNote.textContent = "First frame shown. The same masking applies to every frame of the clip.";
    } else {
      el.previewNote.textContent = "DICOM can't be previewed in the browser. The header tags are removed and the band below is blacked out on the server.";
    }
  });

  function drawPreview() {
    const c = el.canvas, ctx = c.getContext("2d");
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, c.width, c.height);
    if (previewSource) {
      const w = previewSource.videoWidth || previewSource.naturalWidth, h = previewSource.videoHeight || previewSource.naturalHeight;
      c.height = Math.round(c.width * h / w);
      ctx.drawImage(previewSource, 0, 0, c.width, c.height);
    }
    ctx.fillStyle = "rgba(0,0,0,1)";
    ctx.fillRect(0, 0, c.width, Math.round(c.height * el.mask.value / 100));
    boxes.forEach((b) => ctx.fillRect(b.x * c.width, b.y * c.height, b.w * c.width, b.h * c.height));
    ctx.strokeStyle = "#3fb6c9"; ctx.setLineDash([4, 3]);
    ctx.strokeRect(0.5, 0.5, c.width - 1, Math.round(c.height * el.mask.value / 100));
    ctx.setLineDash([]);
    if (drag) { ctx.strokeStyle = "#f2b84b"; ctx.strokeRect(drag.x0, drag.y0, drag.x1 - drag.x0, drag.y1 - drag.y0); }
  }
  function canvasPt(e) {
    const r = el.canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) * el.canvas.width / r.width, y: (e.clientY - r.top) * el.canvas.height / r.height };
  }
  el.canvas.addEventListener("mousedown", (e) => { const p = canvasPt(e); drag = { x0: p.x, y0: p.y, x1: p.x, y1: p.y }; });
  el.canvas.addEventListener("mousemove", (e) => { if (!drag) return; const p = canvasPt(e); drag.x1 = p.x; drag.y1 = p.y; drawPreview(); });
  window.addEventListener("mouseup", () => {
    if (!drag) return;
    const W = el.canvas.width, H = el.canvas.height;
    const x = Math.min(drag.x0, drag.x1), y = Math.min(drag.y0, drag.y1);
    const w = Math.abs(drag.x1 - drag.x0), h = Math.abs(drag.y1 - drag.y0);
    if (w > 4 && h > 4) boxes.push({ x: x / W, y: y / H, w: w / W, h: h / H });
    drag = null; drawPreview();
  });

  el.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = el.file.files[0];
    if (!state.region) { el.uploadErr.textContent = "Tap the body to choose the anterior or lateral chest."; return; }
    if (!state.probe) { el.uploadErr.textContent = "Choose the probe you used."; return; }
    if (!f) { el.uploadErr.textContent = "Choose a file first."; return; }
    const fd = new FormData();
    fd.append("file", f); fd.append("region", state.region); fd.append("probe", state.probe);
    fd.append("head_side", state.head);
    fd.append("header_pct", el.mask.value);
    fd.append("boxes", JSON.stringify(boxes)); fd.append("patient_id", el.patient.value.trim());
    el.confirm.disabled = true; el.confirm.textContent = "De-identifying…"; el.uploadErr.textContent = "";
    try {
      const res = await (await api("/api/scans", { method: "POST", body: fd })).json();
      el.dialog.close();
      await loadScan(res.scan_id);
    } catch (err) {
      el.uploadErr.textContent = err.message;
    } finally {
      el.confirm.disabled = false; el.confirm.textContent = "De-identify & load";
    }
  });

  // ---------------- scan loading & playback ----------------
  async function loadScan(scanId) {
    stopPlayback();
    state.frames.forEach((u) => URL.revokeObjectURL(u));
    const info = await (await api(`/api/scans/${scanId}`)).json();
    state.scan = info; state.idx = 0; state.feedback = info.feedback || [];
    state.viewName = info.region_name || cfg.views[info.target_view] || info.target_view;
    el.monView.textContent = `${state.viewName} · ${probeName(info.probe)} probe` +
      (info.head_side === "right" ? " · head on right" : "");
    showReference(cfg.views[info.target_view] ? info.target_view : null);
    el.monFrame.textContent = "loading…";
    state.frames = [];
    for (let i = 0; i < info.frame_count; i++) {
      const blob = await (await api(`/api/scans/${scanId}/frames/${i}`)).blob();
      state.frames.push(URL.createObjectURL(blob));
      if (i === 0) showFrame(0);
    }
    el.scrub.max = info.frame_count - 1; el.scrub.disabled = info.frame_count < 2;
    [el.play, el.step].forEach((b) => (b.disabled = info.frame_count < 2));
    el.analyze.disabled = false;
    el.empty.hidden = true; el.img.hidden = false;
    renderPrivacy(info);
    renderTimeline();
    history.replaceState(null, "", `#scan=${scanId}`);
    resetCoachPanel();
    if (state.feedback.length) renderFeedback(state.feedback[state.feedback.length - 1]);
    setTestButton();
    if (info.frame_count > 1) startPlayback();
    else setLive(true);
    // No automatic grading: the coach runs once when the learner presses Test, and again only on Re-evaluate.
  }

  function showFrame(i) {
    state.idx = i;
    el.img.src = state.frames[i];
    el.scrub.value = i;
    const n = state.scan?.frame_count || 1;
    el.monFrame.textContent = n > 1 ? `frame ${i + 1}/${n} · ${cfg.fps} fps` : "still image";
  }
  function setLive(on) {
    el.live.textContent = on ? "● LIVE (simulated)" : "❚❚ PAUSED";
    el.live.classList.toggle("on", on);
  }
  function startPlayback() {
    if (!state.scan || state.scan.frame_count < 2) return;
    state.playing = true; el.play.textContent = "❚❚"; setLive(true);
    state.playTimer = setInterval(() => showFrame((state.idx + 1) % state.scan.frame_count), 1000 / cfg.fps);
  }
  function stopPlayback() {
    state.playing = false; el.play.textContent = "▶";
    clearInterval(state.playTimer);
    if (state.scan) setLive(false);
  }
  function setTestButton() {
    const clip = state.scan && state.scan.frame_count > 1;
    el.analyze.textContent = state.feedback.length ? "Re-evaluate" : clip ? "Test this frame" : "Test image";
    el.analyze.title = clip ? "Runs the coach on the frame on screen (pause or scrub to choose it)" : "";
  }
  el.play.addEventListener("click", () => (state.playing ? stopPlayback() : startPlayback()));
  el.step.addEventListener("click", () => { stopPlayback(); showFrame((state.idx + 1) % state.scan.frame_count); });
  el.scrub.addEventListener("input", () => { stopPlayback(); showFrame(parseInt(el.scrub.value, 10)); });
  el.analyze.addEventListener("click", coachNow);
  document.addEventListener("keydown", (e) => {
    if (!state.scan || el.dialog.open || ["INPUT", "SELECT"].includes(document.activeElement?.tagName)) return;
    if (e.code === "Space") { e.preventDefault(); state.playing ? stopPlayback() : startPlayback(); }
    if (e.code === "ArrowRight") { stopPlayback(); showFrame((state.idx + 1) % state.scan.frame_count); }
  });

  // ---------------- coach ----------------
  async function coachNow() {
    if (!state.scan || state.inflight) return;   // never stack requests: limits cost and keeps feedback current
    state.inflight = true; el.analyze.disabled = true; el.analyze.textContent = "Testing…";
    try {
      const res = await (await api(`/api/scans/${state.scan.scan_id}/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frame_index: state.idx }) })).json();
      state.feedback.push(res);
      renderFeedback(res); renderTimeline();
    } catch (err) {
      el.notice.hidden = false; el.notice.textContent = `Coach unavailable: ${err.message}`;
    } finally {
      state.inflight = false; el.analyze.disabled = false; setTestButton();
    }
  }

  function resetCoachPanel() {
    el.notice.hidden = true;
    el.viewTarget.innerHTML = `Region: <strong>${esc(state.viewName)}</strong> · probe: <strong>${esc(probeName(state.scan?.probe))}</strong>` +
      (state.feedback.length ? "" : '<br><span class="muted small">Press Test to get a verdict.</span>');
    el.structures.innerHTML = ""; el.probe.innerHTML = '<li class="muted">Waiting for a frame…</li>';
    el.settings.innerHTML = '<li class="muted">Waiting for a frame…</li>';
    el.gradeBig.innerHTML = "–<small>/10</small>"; el.gradeBand.textContent = "Not graded yet";
    el.subscores.innerHTML = ""; el.gradeBadge.hidden = true;
    el.teaching.textContent = "Findings explanations appear here.";
    el.headline.hidden = true; el.flags.hidden = true; el.observations.innerHTML = "";
    el.routing.innerHTML = ""; el.agentTable.innerHTML = "";
  }

  function renderFeedback(r) {
    el.notice.hidden = !r.notice; el.notice.textContent = r.notice || "";
    if (r.view?.target_id) showReference(r.view.target_id);
    el.headline.hidden = !r.headline; el.headline.innerHTML = r.headline ? `<span>Coach</span>${esc(r.headline)}` : "";
    el.headline.classList.toggle("warn", !!(r.grade && (r.grade.stopped || r.grade.total <= 3)));
    const flags = r.safety?.flags || [];
    el.flags.hidden = !flags.length; el.flags.innerHTML = flags.map((f) => `⚠ ${esc(f)}`).join("<br>");
    el.observations.innerHTML = (r.observations || []).map((o) => `<li>${esc(o)}</li>`).join("");
    el.routing.innerHTML = (r.routing || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const ag = r.agents || {};
    el.agentTable.innerHTML = Object.keys(ag).length ? "<tr><th>Agent</th><th>Time</th><th>Tokens in (cached)</th><th>Out</th><th>Cost</th></tr>" +
      Object.entries(ag).map(([k, v]) => `<tr><td>${esc(k.replace(/_/g, " "))}</td><td>${v.error ? "error" : (v.latency_s ?? "–") + " s"}</td>` +
        `<td>${v.input_tokens ?? "–"} (${v.cached_input_tokens ?? 0})</td><td>${v.output_tokens ?? "–"}</td><td>$${(v.cost_usd ?? 0).toFixed(5)}</td></tr>`).join("") : "";
    const v = r.view || {};
    const rt = r.router;
    el.viewTarget.innerHTML =
      `Region: <strong>${esc(state.viewName)}</strong> · probe: <strong>${esc(probeName(r.probe ?? state.scan?.probe))}</strong>` +
      `<br>${rt ? "View the AI identified" : "Target view"}: <strong>${esc(v.target_name || "")}</strong>` +
      (rt ? ` <span class="muted">(${esc(rt.confidence)}: ${esc(rt.reason)})</span>` : "") +
      (v.detected && !v.matches_target ? `<br>Identifier check: <strong>${esc(v.detected)}</strong> ✕` : "");
    el.structures.innerHTML = "";
    (r.structures || []).forEach((s) => {
      const item = li(`${esc(s.name)}`, s.seen === true ? "seen" : s.seen === false ? "missing" : "");
      if (s.detail) item.title = s.detail;
      el.structures.appendChild(item);
    });
    el.probe.innerHTML = "";
    (r.probe_guidance || []).forEach((p) => el.probe.appendChild(
      li(`${p.issue ? `<span class="issue">If: ${esc(p.issue)}</span>` : ""}<span class="action">${esc(p.action)}</span>`)));
    if (!el.probe.children.length) el.probe.appendChild(li("No probe change needed.", "muted"));
    el.settings.innerHTML = "";
    (r.settings || []).forEach((s) => el.settings.appendChild(li(`<span class="action">${esc(s.advice)}</span>`)));
    if (!el.settings.children.length) el.settings.appendChild(li("Settings look fine.", "muted"));

    const g = r.grade;
    if (g) {
      el.gradeBig.innerHTML = `${g.total}<small>/10</small>`; el.gradeBand.textContent = g.band;
      el.gradeBadge.hidden = false; el.gradeBadge.textContent = `${g.total}/10`;
      el.gradeBadge.className = `grade-badge ${gradeClass(g.total)}`;
      const labels = { landmarks: "Landmarks", orientation: "Orientation & centering", depth: "Depth", gain_focus: "Gain & focus", interpretability: "Interpretability" };
      el.subscores.innerHTML = Object.entries(g.subscores).map(([k, val]) =>
        `<div class="sub${val == null ? " not-scored" : ""}"><span>${labels[k] || k}${(g.weights?.[k] ?? 1) > 1 ? ` (×${g.weights[k]})` : ""}</span><span class="bar"><i class="w${val ?? 0}"></i></span><span>${val == null ? "not scored" : val + "/2"}</span></div>`).join("") +
        (g.gates || []).map((x) => `<div class="muted small">⚠ ${esc(x)}</div>`).join("");
      el.subscores.querySelectorAll(".bar i").forEach((i) => { i.style.width = `${parseInt(i.className.slice(1), 10) * 50}%`; });
    } else {
      el.gradeBig.innerHTML = "–<small>/10</small>";
      el.gradeBand.textContent = r.mode === "demo" ? "Grading starts when the AI agents are connected." : "Not graded";
      el.gradeBadge.hidden = true; el.subscores.innerHTML = "";
    }
    el.teaching.innerHTML = (r.teaching || []).length ? r.teaching.map((t) => `<p>${esc(t)}</p>`).join("")
      : '<span class="muted">No teaching point for this frame.</span>';
    const u = r.usage || {};
    el.usage.textContent = `last check: ${u.latency_ms != null ? (u.latency_ms / 1000).toFixed(1) + " s" : "–"} · tokens in ${u.input_tokens ?? 0} (cached ${u.cached_input_tokens ?? 0}) / out ${u.output_tokens ?? 0} · $${(u.cost_usd ?? 0).toFixed(4)}`;
  }

  function renderTimeline() {
    el.timeline.innerHTML = "";
    if (!state.feedback.length) { el.timeline.innerHTML = '<span class="muted">Each Test or Re-evaluate adds a grade here.</span>'; return; }
    state.feedback.forEach((f) => {
      const b = document.createElement("span");
      const g = f.grade?.total;
      b.className = `tl-bar ${gradeClass(g)}`;
      b.style.height = `${g ? 8 + g * 5.6 : 8}px`;
      b.title = `Frame ${f.frame_index + 1}: ${g ? g + "/10" : "not graded"}`;
      b.addEventListener("click", () => { stopPlayback(); showFrame(f.frame_index); renderFeedback(f); });
      el.timeline.appendChild(b);
    });
  }

  function renderPrivacy(info) {
    const d = info.deid_report || {};
    const removed = (d.metadata_removed || []).length ? d.metadata_removed.join(", ") : "no metadata found";
    el.privacy.innerHTML =
      `Header band blacked out: <strong>${esc(d.header_band_pct)}%</strong> · extra boxes: ${esc(d.extra_boxes)}<br>` +
      `Metadata removed: ${esc(removed)}<br>` +
      `Patient reference: <code>${esc(info.patient_ref || "none")}</code> (keyed pseudonym)<br>` +
      `Stored encrypted (AES-256-GCM). Scan ID <code>${esc(info.scan_id.slice(0, 8))}…</code>`;
  }

  // Open a scan from the history page (#scan=<id>)
  const m = location.hash.match(/scan=([a-f0-9]{32})/);
  if (m) loadScan(m[1]).catch((e) => { el.notice.hidden = false; el.notice.textContent = e.message; });
})();
