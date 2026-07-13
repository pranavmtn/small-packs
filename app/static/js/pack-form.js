/**
 * Fast pack entry: shortcuts, photo preview, location preview,
 * remember last location & age.
 */
(function () {
  "use strict";

  const form = document.getElementById("packForm");
  if (!form) return;

  const STORAGE_KEYS = {
    location: "packs.lastLocation",
    ageYears: "packs.lastAgeYears",
    ageMonths: "packs.lastAgeMonths",
    locations: "packs.recentLocations",
  };

  const nameInput = document.getElementById("name");
  const locationInput = document.getElementById("location");
  const ageYears = document.getElementById("age_years");
  const ageMonths = document.getElementById("age_months");
  const locationPreview = document.getElementById("locationPreview");
  const locationSuggestions = document.getElementById("locationSuggestions");
  const photoInput = document.getElementById("photo");
  const photoCamera = document.getElementById("photoCamera");
  const photoPreviewImg = document.getElementById("photoPreviewImg");
  const photoEmpty = document.getElementById("photoEmpty");
  const btnSave = document.getElementById("btnSave");
  const btnSaveNext = document.getElementById("btnSaveNext");
  const mode = form.dataset.mode;
  const clearPrefs = form.dataset.clearPrefs === "1";

  // --- Preferences ---------------------------------------------------------

  function loadPrefs() {
    if (mode !== "add") return;
    if (clearPrefs) {
      localStorage.removeItem(STORAGE_KEYS.location);
      localStorage.removeItem(STORAGE_KEYS.ageYears);
      localStorage.removeItem(STORAGE_KEYS.ageMonths);
      return;
    }

    if (locationInput && !locationInput.value) {
      const last = localStorage.getItem(STORAGE_KEYS.location);
      if (last) locationInput.value = last;
    }
    if (ageYears && !ageYears.value) {
      const y = localStorage.getItem(STORAGE_KEYS.ageYears);
      if (y !== null) ageYears.value = y;
    }
    if (ageMonths && !ageMonths.value) {
      const m = localStorage.getItem(STORAGE_KEYS.ageMonths);
      if (m !== null) ageMonths.value = m;
    }
  }

  function savePrefs() {
    if (mode !== "add") return;
    if (locationInput && locationInput.value.trim()) {
      localStorage.setItem(STORAGE_KEYS.location, locationInput.value.trim());
      rememberLocation(locationInput.value.trim());
    }
    if (ageYears) {
      localStorage.setItem(STORAGE_KEYS.ageYears, ageYears.value || "");
    }
    if (ageMonths) {
      localStorage.setItem(STORAGE_KEYS.ageMonths, ageMonths.value || "");
    }
  }

  function rememberLocation(text) {
    let list = [];
    try {
      list = JSON.parse(localStorage.getItem(STORAGE_KEYS.locations) || "[]");
    } catch (e) {
      list = [];
    }
    list = list.filter(function (item) {
      return item !== text;
    });
    list.unshift(text);
    list = list.slice(0, 8);
    localStorage.setItem(STORAGE_KEYS.locations, JSON.stringify(list));
    renderSuggestions(list);
  }

  function renderSuggestions(list) {
    if (!locationSuggestions) return;
    locationSuggestions.innerHTML = "";
    (list || []).forEach(function (item) {
      const opt = document.createElement("option");
      opt.value = item;
      locationSuggestions.appendChild(opt);
    });
  }

  function loadSuggestions() {
    try {
      const list = JSON.parse(localStorage.getItem(STORAGE_KEYS.locations) || "[]");
      renderSuggestions(list);
    } catch (e) {
      /* ignore */
    }
  }

  // --- Location preview (mirrors server heuristics lightly) ----------------

  const POSITION_WORDS = new Set([
    "first", "second", "third", "fourth", "fifth",
    "top", "bottom", "middle", "upper", "lower",
    "left", "right", "front", "back", "inner", "outer",
  ]);
  const CONTAINER_WORDS = new Set([
    "box", "boxes", "shelf", "shelves", "level", "levels",
    "drawer", "drawers", "cabinet", "cabinets", "cupboard", "cupboards",
    "closet", "closets", "bin", "bins", "bag", "bags", "rack", "racks",
    "row", "rows", "column", "columns", "compartment", "crate", "crates",
    "trunk", "locker", "room", "area", "section", "zone", "aisle", "bay",
    "slot", "hook", "wall", "floor", "ceiling", "corner", "side", "stack",
  ]);

  function titleCase(text) {
    return text
      .split(/\s+/)
      .filter(Boolean)
      .map(function (w, i) {
        const lower = w.toLowerCase();
        if (i > 0 && ["a", "an", "the", "of", "and", "in", "on", "at", "to", "for"].includes(lower)) {
          return lower;
        }
        return lower.charAt(0).toUpperCase() + lower.slice(1);
      })
      .join(" ");
  }

  function parseLocationClient(text) {
    const cleaned = (text || "").trim().replace(/\s+/g, " ");
    if (!cleaned) return [];

    if (/[>/|→,]|(->)/.test(cleaned)) {
      return cleaned
        .split(/\s*(?:>|\/|\||→|->|,)\s*/)
        .filter(Boolean)
        .map(titleCase);
    }

    const tokens = cleaned.toLowerCase().split(" ");
    const starts = [];
    let i = 0;
    while (i < tokens.length) {
      if (i + 1 < tokens.length) {
        const a = tokens[i];
        const b = tokens[i + 1].replace(/s$/, "");
        if (POSITION_WORDS.has(a) && CONTAINER_WORDS.has(b) || CONTAINER_WORDS.has(tokens[i + 1])) {
          if (POSITION_WORDS.has(a) && (CONTAINER_WORDS.has(b) || CONTAINER_WORDS.has(tokens[i + 1]))) {
            starts.push(i);
            i += 2;
            continue;
          }
        }
      }
      const word = tokens[i].replace(/s$/, "");
      if (CONTAINER_WORDS.has(word) && i > 0) {
        if (i > 0 && POSITION_WORDS.has(tokens[i - 1])) {
          if (starts.indexOf(i - 1) === -1) starts.push(i - 1);
        } else {
          starts.push(i);
        }
      }
      i += 1;
    }

    if (!starts.length) {
      if (tokens.length <= 3) return [titleCase(cleaned)];
      return [titleCase(tokens[0]), titleCase(tokens.slice(1).join(" "))];
    }

    starts.sort(function (a, b) { return a - b; });
    const parts = [];
    const first = starts[0];
    if (first > 0) parts.push(titleCase(tokens.slice(0, first).join(" ")));
    starts.forEach(function (start, idx) {
      const end = idx + 1 < starts.length ? starts[idx + 1] : tokens.length;
      parts.push(titleCase(tokens.slice(start, end).join(" ")));
    });
    return parts.filter(Boolean);
  }

  function updateLocationPreview() {
    if (!locationPreview || !locationInput) return;
    const parts = parseLocationClient(locationInput.value);
    if (!parts.length) {
      locationPreview.innerHTML = "";
      return;
    }
    locationPreview.innerHTML =
      '<span class="text-muted me-1">Will save as:</span> ' +
      parts.map(function (p) {
        return '<span class="chip">' + escapeHtml(p) + "</span>";
      }).join('<span class="text-muted">›</span>');
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // --- Photo preview -------------------------------------------------------

  function previewFile(file) {
    if (!file || !photoPreviewImg) return;
    const url = URL.createObjectURL(file);
    photoPreviewImg.src = url;
    photoPreviewImg.classList.remove("d-none");
    if (photoEmpty) photoEmpty.classList.add("d-none");
  }

  function onPhotoChange(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    // Keep a single file input named "photo" for the server
    if (event.target === photoCamera && photoInput) {
      const dt = new DataTransfer();
      dt.items.add(file);
      photoInput.files = dt.files;
    }
    previewFile(file);
  }

  // --- Keyboard shortcuts --------------------------------------------------

  function isTextarea(el) {
    return el && el.tagName === "TEXTAREA";
  }

  document.addEventListener("keydown", function (event) {
    if (!form.contains(document.activeElement) && document.activeElement !== document.body) {
      // Still allow shortcuts when focused inside the form
    }

    // Ctrl/Cmd + Enter → Save & Add Next (add mode) or Save (edit)
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      savePrefs();
      if (mode === "add" && btnSaveNext) {
        btnSaveNext.click();
      } else if (btnSave) {
        btnSave.click();
      }
      return;
    }

    // Enter on non-textarea → Save Pack
    if (event.key === "Enter" && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
      if (isTextarea(document.activeElement)) return;
      if (document.activeElement && document.activeElement.tagName === "BUTTON") return;
      if (document.activeElement && document.activeElement.tagName === "A") return;
      if (!form.contains(document.activeElement) && document.activeElement !== document.body) return;
      event.preventDefault();
      savePrefs();
      if (btnSave) btnSave.click();
    }
  });

  form.addEventListener("submit", function () {
    savePrefs();
  });

  // --- Init ----------------------------------------------------------------

  if (photoInput) photoInput.addEventListener("change", onPhotoChange);
  if (photoCamera) photoCamera.addEventListener("change", onPhotoChange);
  if (locationInput) {
    locationInput.addEventListener("input", updateLocationPreview);
    locationInput.addEventListener("change", updateLocationPreview);
  }

  loadPrefs();
  loadSuggestions();
  updateLocationPreview();

  if (nameInput) {
    // Autofocus reliably after load (mobile-friendly)
    setTimeout(function () {
      nameInput.focus();
      nameInput.select();
    }, 50);
  }
})();
