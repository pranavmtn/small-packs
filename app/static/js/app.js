/**
 * Shared Packs UI helpers.
 */
(function () {
  "use strict";

  // Wire delete confirmation modal from any trigger button
  const deleteModal = document.getElementById("deleteModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      if (!button) return;
      const url = button.getAttribute("data-delete-url");
      const name = button.getAttribute("data-delete-name") || "this pack";
      const form = deleteModal.querySelector("#deleteForm");
      const nameEl = deleteModal.querySelector("#deletePackName");
      if (form && url) form.setAttribute("action", url);
      if (nameEl) nameEl.textContent = name;
    });
  }

  // Auto-dismiss flash messages after a short delay
  document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
    setTimeout(function () {
      const instance = bootstrap.Alert.getOrCreateInstance(alert);
      instance.close();
    }, 5000);
  });
})();
