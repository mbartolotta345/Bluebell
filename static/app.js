const API = {
  plants: "/plants",
  plant: (id) => `/plants/${id}`,
  water: (id) => `/plants/${id}/water`,
  species: "/species",
  contact: "/contact",
  googleLogin: "/auth/google",
  logout: "/auth/logout",
  me: "/auth/me",
};

function formatDate(dateStr) {
  if (!dateStr) return "-";
  const datePart = dateStr.split("T")[0];
  const [y, m, d] = datePart.split("-").map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = (data.errors && data.errors.join(", ")) || "Request failed";
    throw new Error(message);
  }
  return data;
}

/* ---------- Add plant form ---------- */

const addForm = document.getElementById("add-plant-form");
const speciesInput = document.getElementById("plant-species");
const speciesOptionsEl = document.getElementById("species-options");
const speciesInfoEl = document.getElementById("species-info");
const speciesInfoSummaryEl = document.getElementById("species-info-summary");
const speciesInfoLinkEl = document.getElementById("species-info-link");
const speciesInfoCloseBtn = document.getElementById("species-info-close");
const fillSuggestedCheckbox = document.getElementById("fill-suggested-checkbox");
const frequencyInput = document.getElementById("plant-frequency");
const sunlightInput = document.getElementById("plant-sunlight");

let speciesGuide = [];
let selectedSpecies = null;

async function loadSpeciesGuide() {
  try {
    speciesGuide = await apiRequest(API.species);
  } catch (err) {
    speciesGuide = [];
    return;
  }
  speciesOptionsEl.innerHTML = speciesGuide
    .map((s) => `<option value="${escapeHtml(s.name)}"></option>`)
    .join("");
}

function fillSuggestedValues(species) {
  frequencyInput.value = species.watering_frequency_days;
  sunlightInput.value = species.sunlight_needs;
}

function showSpeciesInfo(species) {
  selectedSpecies = species;
  speciesInfoSummaryEl.textContent = species.description;
  speciesInfoLinkEl.href = species.source_url;
  speciesInfoEl.hidden = false;
  // Two rAFs so the browser registers the starting (collapsed) state
  // before the class flips - otherwise the transition doesn't play.
  requestAnimationFrame(() => requestAnimationFrame(() => speciesInfoEl.classList.add("open")));

  if (fillSuggestedCheckbox.checked) {
    fillSuggestedValues(species);
  }
}

function hideSpeciesInfo() {
  selectedSpecies = null;
  speciesInfoEl.classList.remove("open");
  setTimeout(() => {
    if (!speciesInfoEl.classList.contains("open")) speciesInfoEl.hidden = true;
  }, 400);
}

speciesInput.addEventListener("input", () => {
  const typed = speciesInput.value.trim().toLowerCase();
  const match = speciesGuide.find((s) => s.name.toLowerCase() === typed);
  if (match) {
    showSpeciesInfo(match);
  } else {
    hideSpeciesInfo();
  }
});

speciesInfoCloseBtn.addEventListener("click", hideSpeciesInfo);

fillSuggestedCheckbox.addEventListener("change", () => {
  if (fillSuggestedCheckbox.checked && selectedSpecies) {
    fillSuggestedValues(selectedSpecies);
  }
});

addForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(addForm);
  const usedSuggestion = Boolean(selectedSpecies) && fillSuggestedCheckbox.checked;

  const payload = {
    name: formData.get("name").trim(),
    species: formData.get("species").trim(),
    last_watered_at: formData.get("last_watered_at"),
    watering_frequency_days: Number(formData.get("watering_frequency_days")),
    sunlight_needs: formData.get("sunlight_needs").trim(),
    notes: formData.get("notes")?.trim() || null,
    used_ai_suggestion: usedSuggestion,
    ai_explanation: usedSuggestion ? selectedSpecies.description : null,
    ai_sources: usedSuggestion ? [selectedSpecies.source_url] : [],
  };

  try {
    await apiRequest(API.plants, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    addForm.reset();
    hideSpeciesInfo();
    fillSuggestedCheckbox.checked = false;
    loadPlants();
  } catch (err) {
    alert(`Could not save plant: ${err.message}`);
  }
});

/* ---------- Report / plant list ---------- */

const plantsList = document.getElementById("plants-list");

function plantCardHtml(plant) {
  const thirstyClass = plant.is_thirsty ? "plant-card thirsty" : "plant-card";
  const thirstyFlag = plant.is_thirsty
    ? `<span class="thirsty-flag" title="Needs water">💧</span>`
    : "";

  return `
    <div class="${thirstyClass}" data-id="${plant.id}">
      <div class="plant-card-header">
        <div>
          <div class="plant-name">${escapeHtml(plant.name)} ${thirstyFlag}</div>
          <div class="plant-species">${escapeHtml(plant.species)}</div>
        </div>
      </div>
      <div class="plant-meta">
        <div><span class="label">Watering frequency</span>Every ${plant.watering_frequency_days} day(s)</div>
        <div><span class="label">Sunlight needs</span>${escapeHtml(plant.sunlight_needs)}</div>
        <div><span class="label">Last watered</span>${formatDate(plant.last_watered_at)}</div>
        <div><span class="label">Next watering due</span>${formatDate(plant.next_due_date)}</div>
      </div>
      ${plant.notes ? `<div class="plant-notes">${escapeHtml(plant.notes)}</div>` : ""}
      <div class="plant-actions">
        <button class="btn-small water" data-action="water" data-id="${plant.id}">Mark watered</button>
        <button class="btn-small" data-action="edit" data-id="${plant.id}">Edit</button>
        <button class="btn-small danger" data-action="remove" data-id="${plant.id}">Remove</button>
      </div>
      <div class="edit-container" data-edit-for="${plant.id}"></div>
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function editFormHtml(plant) {
  return `
    <form class="edit-form" data-edit-id="${plant.id}">
      <div class="field">
        <label>Name</label>
        <input type="text" name="name" value="${escapeHtml(plant.name)}" required />
      </div>
      <div class="field">
        <label>Species</label>
        <input type="text" name="species" value="${escapeHtml(plant.species)}" required />
      </div>
      <div class="field">
        <label>Watering frequency (days)</label>
        <input type="number" name="watering_frequency_days" min="1" value="${plant.watering_frequency_days}" required />
      </div>
      <div class="field">
        <label>Sunlight needs</label>
        <input type="text" name="sunlight_needs" value="${escapeHtml(plant.sunlight_needs)}" required />
      </div>
      <div class="field">
        <label>Last watered</label>
        <input type="date" name="last_watered_at" value="${plant.last_watered_at.split("T")[0]}" required />
      </div>
      <div class="field">
        <label>Notes</label>
        <textarea name="notes" rows="2">${escapeHtml(plant.notes || "")}</textarea>
      </div>
      <div class="plant-actions">
        <button type="submit" class="btn-small water">Save changes</button>
        <button type="button" class="btn-small" data-action="cancel-edit" data-id="${plant.id}">Cancel</button>
      </div>
    </form>
  `;
}

let plantsCache = [];

async function loadPlants() {
  try {
    plantsCache = await apiRequest(API.plants);
  } catch (err) {
    plantsList.innerHTML = `<p class="empty-state">Could not load plants: ${err.message}</p>`;
    return;
  }

  if (plantsCache.length === 0) {
    plantsList.innerHTML = `<p class="empty-state" id="empty-state">No plants yet - add one above!</p>`;
    return;
  }

  plantsList.innerHTML = plantsCache.map(plantCardHtml).join("");
}

plantsList.addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const { action, id } = btn.dataset;

  if (action === "water") {
    try {
      await apiRequest(API.water(id), { method: "POST" });
      loadPlants();
    } catch (err) {
      alert(`Could not mark watered: ${err.message}`);
    }
  } else if (action === "remove") {
    if (!confirm("Remove this plant?")) return;
    try {
      await apiRequest(API.plant(id), { method: "DELETE" });
      loadPlants();
    } catch (err) {
      alert(`Could not remove plant: ${err.message}`);
    }
  } else if (action === "edit") {
    const plant = plantsCache.find((p) => String(p.id) === String(id));
    const container = plantsList.querySelector(`.edit-container[data-edit-for="${id}"]`);
    if (plant && container) container.innerHTML = editFormHtml(plant);
  } else if (action === "cancel-edit") {
    const container = plantsList.querySelector(`.edit-container[data-edit-for="${id}"]`);
    if (container) container.innerHTML = "";
  }
});

plantsList.addEventListener("submit", async (e) => {
  const form = e.target.closest("form[data-edit-id]");
  if (!form) return;
  e.preventDefault();

  const id = form.dataset.editId;
  const formData = new FormData(form);
  const payload = {
    name: formData.get("name").trim(),
    species: formData.get("species").trim(),
    watering_frequency_days: Number(formData.get("watering_frequency_days")),
    sunlight_needs: formData.get("sunlight_needs").trim(),
    last_watered_at: formData.get("last_watered_at"),
    notes: formData.get("notes")?.trim() || null,
  };

  try {
    await apiRequest(API.plant(id), {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    loadPlants();
  } catch (err) {
    alert(`Could not save changes: ${err.message}`);
  }
});

/* ---------- Contact info ---------- */

const contactForm = document.getElementById("contact-form");
const contactStatus = document.getElementById("contact-status");

async function loadContact() {
  try {
    const contact = await apiRequest(API.contact);
    contactForm.phone_number.value = contact.phone_number || "";
    contactForm.email.value = contact.email || "";
  } catch (err) {
    contactStatus.textContent = "Could not load contact info.";
  }
}

contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(contactForm);
  const payload = {
    phone_number: formData.get("phone_number")?.trim() || null,
    email: formData.get("email")?.trim() || null,
  };

  try {
    await apiRequest(API.contact, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    contactStatus.textContent = "Saved!";
    setTimeout(() => (contactStatus.textContent = ""), 2500);
  } catch (err) {
    contactStatus.textContent = `Could not save: ${err.message}`;
  }
});

/* ---------- Auth ----------
   The plant tracker (add/view/edit/water plants) works for everyone,
   logged in or not. Only the Reminders section - which needs to know
   who to contact - requires signing in with Google. */

const loginPrompt = document.getElementById("login-prompt");
const userInfo = document.getElementById("user-info");
const userEmailEl = document.getElementById("user-email");
const logoutBtn = document.getElementById("logout-btn");
const contactFormEl = document.getElementById("contact-form");

function showLoggedIn(user) {
  loginPrompt.hidden = true;
  userInfo.hidden = false;
  contactFormEl.hidden = false;
  userEmailEl.textContent = user.email;
  loadContact();
}

function showLoggedOut() {
  loginPrompt.hidden = false;
  userInfo.hidden = true;
  contactFormEl.hidden = true;
}

async function checkAuth() {
  try {
    const result = await apiRequest(API.me);
    if (result.logged_in) {
      showLoggedIn(result);
    } else {
      showLoggedOut();
    }
  } catch (err) {
    showLoggedOut();
  }
}

window.handleGoogleCredential = async (response) => {
  try {
    const user = await apiRequest(API.googleLogin, {
      method: "POST",
      body: JSON.stringify({ credential: response.credential }),
    });
    showLoggedIn(user);
  } catch (err) {
    alert(`Could not log in: ${err.message}`);
  }
};

logoutBtn.addEventListener("click", async () => {
  try {
    await apiRequest(API.logout, { method: "POST" });
  } catch (err) {
    // ignore - clear the UI regardless
  }
  showLoggedOut();
});

/* ---------- Init ---------- */

loadPlants();
loadSpeciesGuide();
checkAuth();
