document.querySelectorAll(".js-delete").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!confirm("Delete this scan and its feedback permanently? This cannot be undone.")) return;
    try {
      await api(`/api/scans/${btn.dataset.scan}`, { method: "DELETE" });
      btn.closest("tr").remove();
    } catch (e) { alert(e.message); }
  });
});
