const form = document.querySelector("#recommendation-form");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#result-count");
const formError = document.querySelector("#form-error");
const resultsPanel = document.querySelector(".results-panel");
const submitButton = form.querySelector("button[type='submit']");
const profileAvatar = document.querySelector("#profile-avatar");
const profileName = document.querySelector("#profile-name");
const profileStatus = document.querySelector("#profile-status");
const previousProfileButton = document.querySelector("#previous-profile");
const nextProfileButton = document.querySelector("#next-profile");

let profiles = [];
let activeProfileIndex = 0;
let lastSearch = null;
let requestSequence = 0;

const labels = {
  red: "Красное",
  white: "Белое",
  rose: "Розовое",
  dry: "Сухое",
  semi_dry: "Полусухое",
  semi_sweet: "Полусладкое",
  sweet: "Сладкое",
};

function buildQuery(data) {
  const parts = [];
  if (data.get("color")) parts.push(data.get("color"));
  if (data.get("sugarType")) parts.push(data.get("sugarType"));

  const minPrice = data.get("minPrice");
  const maxPrice = data.get("maxPrice");
  if (minPrice && maxPrice) parts.push(`от ${minPrice} до ${maxPrice}`);
  else if (minPrice) parts.push(`от ${minPrice}`);
  else if (maxPrice) parts.push(`до ${maxPrice}`);

  if (data.get("rating")) parts.push(`рейтинг от ${data.get("rating")}`);
  return parts.join(" ") || "покажи вино";
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = value ?? "";
  return element.innerHTML;
}

function formatPrice(value) {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(value);
}

function safeUrl(value) {
  if (!value) return null;
  try {
    const url = new URL(value, window.location.origin);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function cardTemplate(wine, index) {
  const tags = [wine.color, wine.sugar_type, wine.country, wine.grape]
    .filter(Boolean)
    .map((value) => `<li>${escapeHtml(labels[value] || value)}</li>`)
    .join("");
  const imageUrl = safeUrl(wine.image_url);
  const storeUrl = safeUrl(wine.product_url);
  const image = imageUrl
    ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(wine.name)}" loading="lazy" />`
    : '<span class="wine-placeholder" aria-hidden="true">V</span>';
  const rating = wine.rating ? `★ ${wine.rating.toFixed(1)}` : "Без рейтинга";
  const link = storeUrl
    ? `<a class="store-link" href="${escapeHtml(storeUrl)}" target="_blank" rel="noopener noreferrer">В магазин ↗</a>`
    : '<span class="store-link disabled">Нет ссылки</span>';

  return `
    <article class="wine-card" style="animation-delay: ${index * 45}ms">
      <div class="wine-image">${image}</div>
      <div class="wine-info">
        <p class="wine-meta">${escapeHtml(wine.brand || "Винная подборка")}</p>
        <h3>${escapeHtml(wine.name)}</h3>
        <ul class="characteristics">${tags}</ul>
      </div>
      <div class="wine-action">
        <span class="rating">${rating}</span>
        <strong class="price">${formatPrice(wine.price)} ₽</strong>
        ${link}
      </div>
    </article>`;
}

function showEmpty(message) {
  results.innerHTML = `
    <div class="empty-state">
      <span class="empty-icon" aria-hidden="true">⌁</span>
      <h3>Ничего не нашлось</h3>
      <p>${escapeHtml(message)}</p>
    </div>`;
}

function activeProfile() {
  return profiles[activeProfileIndex] || null;
}

function updateProfileDisplay() {
  const profile = activeProfile();
  if (!profile) {
    profileAvatar.textContent = "—";
    profileName.textContent = "Без профиля";
    profileStatus.textContent = "Общая подборка";
    return;
  }

  const name = profile.username || `Профиль ${profile.id}`;
  profileAvatar.textContent = name.trim().charAt(0).toLocaleUpperCase("ru-RU");
  profileName.textContent = name;
  profileStatus.textContent = `Профиль ${activeProfileIndex + 1} из ${profiles.length}`;
}

async function loadProfiles() {
  try {
    const response = await fetch("/users?limit=100");
    if (!response.ok) throw new Error("Не удалось загрузить профили");
    profiles = await response.json();
  } catch {
    profiles = [];
  }

  updateProfileDisplay();
  const canSwitch = profiles.length > 1;
  previousProfileButton.disabled = !canSwitch;
  nextProfileButton.disabled = !canSwitch;
  if (profiles.length && lastSearch) requestRecommendations(lastSearch);
}

function switchProfile(direction) {
  if (profiles.length < 2) return;
  activeProfileIndex = (activeProfileIndex + direction + profiles.length) % profiles.length;
  updateProfileDisplay();
  if (lastSearch) requestRecommendations(lastSearch);
}

async function requestRecommendations(search) {
  const currentRequest = ++requestSequence;
  const profile = activeProfile();
  submitButton.disabled = true;
  submitButton.firstElementChild.textContent = "Подбираем…";
  resultsPanel.setAttribute("aria-busy", "true");
  results.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';

  try {
    const response = await fetch("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...search,
        user_id: profile?.id,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Не удалось получить рекомендации");
    if (currentRequest !== requestSequence) return;

    const recommendations = payload.recommendations;
    resultCount.textContent = `${recommendations.length} ${recommendations.length === 1 ? "вариант" : "вариантов"}`;
    if (recommendations.length === 0) {
      showEmpty("Попробуйте расширить диапазон цены или изменить выбранные параметры.");
    } else {
      results.innerHTML = recommendations.map(cardTemplate).join("");
    }
  } catch (error) {
    if (currentRequest !== requestSequence) return;
    resultCount.textContent = "0 вариантов";
    showEmpty(error.message || "Сервис временно недоступен. Попробуйте ещё раз.");
  } finally {
    if (currentRequest === requestSequence) {
      submitButton.disabled = false;
      submitButton.firstElementChild.textContent = "Подобрать вино";
      resultsPanel.setAttribute("aria-busy", "false");
    }
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  formError.hidden = true;
  const data = new FormData(form);
  const minPrice = Number(data.get("minPrice") || 0);
  const maxPrice = Number(data.get("maxPrice") || 0);
  if (minPrice && maxPrice && minPrice > maxPrice) {
    formError.textContent = "Минимальная цена не может быть выше максимальной.";
    formError.hidden = false;
    return;
  }

  lastSearch = {
    query: buildQuery(data),
    limit: Number(data.get("limit")),
  };
  requestRecommendations(lastSearch);
});

previousProfileButton.addEventListener("click", () => switchProfile(-1));
nextProfileButton.addEventListener("click", () => switchProfile(1));

loadProfiles();
