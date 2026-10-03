const form = document.querySelector("#recommendation-form");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#result-count");
const formError = document.querySelector("#form-error");
const resultsPanel = document.querySelector(".results-panel");
const submitButton = form.querySelector("button[type='submit']");

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

form.addEventListener("submit", async (event) => {
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

  submitButton.disabled = true;
  submitButton.firstElementChild.textContent = "Подбираем…";
  resultsPanel.setAttribute("aria-busy", "true");
  results.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';

  try {
    const response = await fetch("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: buildQuery(data),
        limit: Number(data.get("limit")),
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Не удалось получить рекомендации");

    const recommendations = payload.recommendations;
    resultCount.textContent = `${recommendations.length} ${recommendations.length === 1 ? "вариант" : "вариантов"}`;
    if (recommendations.length === 0) {
      showEmpty("Попробуйте расширить диапазон цены или изменить выбранные параметры.");
    } else {
      results.innerHTML = recommendations.map(cardTemplate).join("");
    }
  } catch (error) {
    resultCount.textContent = "0 вариантов";
    showEmpty(error.message || "Сервис временно недоступен. Попробуйте ещё раз.");
  } finally {
    submitButton.disabled = false;
    submitButton.firstElementChild.textContent = "Подобрать вино";
    resultsPanel.setAttribute("aria-busy", "false");
  }
});
