// Shared helpers: CSRF-aware fetch and the inactivity sign-out timer.
(function () {
  const meta = (n) => document.querySelector(`meta[name="${n}"]`)?.content || "";
  const csrf = meta("csrf-token");
  let lastServerContact = Date.now();   // the server's idle clock resets on every authenticated request

  window.api = async function (url, opts = {}) {
    opts.headers = Object.assign({ "X-CSRF-Token": csrf }, opts.headers || {});
    opts.credentials = "same-origin";
    const res = await fetch(url, opts);
    if (res.status === 401) { window.location = "/login?msg=Session+expired.+Please+sign+in+again."; throw new Error("401"); }
    lastServerContact = Date.now();
    if (!res.ok) {
      let msg = res.statusText;
      try { msg = (await res.json()).detail || msg; } catch (_) {}
      throw new Error(msg);
    }
    return res;
  };

  const el = document.getElementById("idle-timer");
  if (!el || !csrf) return;
  const idleMs = (parseInt(meta("idle-minutes"), 10) || 15) * 60 * 1000;
  setInterval(() => {
    const left = Math.max(0, idleMs - (Date.now() - lastServerContact));
    const m = Math.floor(left / 60000), s = Math.floor((left % 60000) / 1000);
    el.textContent = `auto sign-out in ${m}:${String(s).padStart(2, "0")}`;
    el.classList.toggle("soon", left < 120000);
    if (left === 0) window.location = "/login?msg=Signed+out+after+inactivity.";
  }, 1000);
})();
