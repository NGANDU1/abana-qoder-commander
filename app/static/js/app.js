// Small shared JS helpers (kept minimal for an academic project prototype).
(function () {
  window.SmartWaste = window.SmartWaste || {};

  // Optional: enable Bootstrap tooltips if used.
  document.addEventListener("DOMContentLoaded", () => {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].forEach(el => new bootstrap.Tooltip(el));
  });
})();
