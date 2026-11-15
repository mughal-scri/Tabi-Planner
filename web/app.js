"use strict";

const LIMITS = { cities: 5, daysPerCity: 5, totalDays: 10 };
const state = {
  cities: [],
  route: [],
  ageGroup: "",
  categories: [],
  interests: new Set(),
  plan: null,
};

const byId = (id) => document.getElementById(id);
const make = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

function announce(message) {
  byId("live-message").textContent = message;
}

function totalDays() {
  return state.route.reduce((total, entry) => total + entry.days, 0);
}

function cityFor(id) {
  return state.cities.find((city) => city.id === id);
}

function updateTripValidation() {
  const total = totalDays();
  const errors = [];
  if (!state.route.length) errors.push("choose at least one city");
  if (!state.ageGroup) errors.push("choose an age group");
  if (state.route.length > LIMITS.cities) errors.push(`use no more than ${LIMITS.cities} cities`);
  if (total > LIMITS.totalDays) errors.push(`use no more than ${LIMITS.totalDays} days in total`);
  if (errors.length) {
    const combined = errors.join(" and ");
    byId("trip-validation").textContent = `${combined.charAt(0).toUpperCase()}${combined.slice(1)} to continue.`;
  } else {
    byId("trip-validation").textContent = "Your trip is ready.";
  }
  byId("trip-continue").disabled = errors.length > 0;
  byId("route-day-count").textContent = `${total} of ${LIMITS.totalDays} days`;
  byId("route-empty").hidden = state.route.length > 0;
}

function renderCities() {
  const list = byId("city-list");
  if (!list.children.length || list.querySelector(".loading-line")) {
    list.replaceChildren();
    for (const city of state.cities) {
      const selected = state.route.some((entry) => entry.city_id === city.id);
      const button = make("button", "city-chip", `${city.name} · ${city.places} places`);
      button.type = "button";
      button.dataset.cityId = city.id;
      button.setAttribute("aria-pressed", String(selected));
      button.setAttribute("aria-label", `${selected ? "Remove" : "Add"} ${city.name}, ${city.region}, ${city.places} places`);
      button.addEventListener("click", () => toggleCity(city.id));
      list.append(button);
    }
    return;
  }
  for (const button of list.querySelectorAll(".city-chip")) {
    const cityId = button.dataset.cityId;
    const city = cityFor(cityId);
    if (!city) continue;
    const selected = state.route.some((entry) => entry.city_id === cityId);
    button.setAttribute("aria-pressed", String(selected));
    button.setAttribute("aria-label", `${selected ? "Remove" : "Add"} ${city.name}, ${city.region}, ${city.places} places`);
  }
}

function renderRoute() {
  const active = document.activeElement;
  let focusTarget = null;
  if (active && active.closest("#route-list")) {
    const row = active.closest(".route-row");
    const cityId = row ? row.dataset.cityId : null;
    let action = null;
    if (active.classList.contains("route-move")) {
      action = active.dataset.action;
    } else if (active.classList.contains("stepper-button")) {
      action = active.dataset.action;
    }
    if (cityId && action) {
      focusTarget = { cityId, action };
    }
  }

  const list = byId("route-list");
  list.replaceChildren();
  state.route.forEach((entry, index) => {
    const city = cityFor(entry.city_id);
    if (!city) return;
    const row = make("li", "route-row");
    row.dataset.cityId = city.id;
    row.append(make("span", "route-number", String(index + 1).padStart(2, "0")));

    const name = make("span", "route-name", city.name);
    name.append(make("span", "route-meta", city.region));
    row.append(name);

    const controls = make("span", "route-controls");
    const moveUp = make("button", "route-move", "↑");
    moveUp.type = "button";
    moveUp.dataset.action = "up";
    moveUp.disabled = index === 0;
    moveUp.setAttribute("aria-label", `Move ${city.name} earlier`);
    moveUp.addEventListener("click", () => moveCity(index, -1));
    const moveDown = make("button", "route-move", "↓");
    moveDown.type = "button";
    moveDown.dataset.action = "down";
    moveDown.disabled = index === state.route.length - 1;
    moveDown.setAttribute("aria-label", `Move ${city.name} later`);
    moveDown.addEventListener("click", () => moveCity(index, 1));
    controls.append(moveUp, moveDown);
    row.append(controls);

    const dayControls = make("span", "route-days");
    const minus = make("button", "stepper-button", "−");
    minus.type = "button";
    minus.dataset.action = "minus";
    minus.disabled = entry.days <= 1;
    minus.setAttribute("aria-label", `Remove a day from ${city.name}`);
    minus.addEventListener("click", () => changeDays(index, -1));
    const count = make("strong", "", String(entry.days));
    count.setAttribute("aria-label", `${entry.days} days`);
    const plus = make("button", "stepper-button", "+");
    plus.type = "button";
    plus.dataset.action = "plus";
    plus.disabled = entry.days >= LIMITS.daysPerCity || totalDays() >= LIMITS.totalDays;
    plus.setAttribute("aria-label", `Add a day to ${city.name}`);
    plus.addEventListener("click", () => changeDays(index, 1));
    dayControls.append(minus, count, plus, make("span", "", "days"));
    row.append(dayControls);
    list.append(row);
  });
  updateTripValidation();

  if (focusTarget) {
    const targetRow = list.querySelector(`[data-city-id="${focusTarget.cityId}"]`);
    if (targetRow) {
      const btn = targetRow.querySelector(`[data-action="${focusTarget.action}"]`);
      if (btn && !btn.disabled) {
        btn.focus();
      } else if (btn && btn.disabled) {
        const altAction =
          focusTarget.action === "plus" ? "minus" :
          focusTarget.action === "minus" ? "plus" :
          focusTarget.action === "up" ? "down" : "up";
        const altBtn = altAction ? targetRow.querySelector(`[data-action="${altAction}"]`) : null;
        if (altBtn && !altBtn.disabled) altBtn.focus();
        else targetRow.focus();
      }
    }
  }
}

function toggleCity(cityId) {
  const index = state.route.findIndex((entry) => entry.city_id === cityId);
  if (index >= 0) {
    state.route.splice(index, 1);
    byId("trip-limit-message").textContent = "";
  } else if (state.route.length >= LIMITS.cities) {
    byId("trip-limit-message").textContent = `A route can include up to ${LIMITS.cities} cities.`;
    announce(`A route can include up to ${LIMITS.cities} cities.`);
    return;
  } else {
    state.route.push({ city_id: cityId, days: 1 });
    byId("trip-limit-message").textContent = "";
  }
  renderCities();
  renderRoute();
  announce("Route updated.");
}

function moveCity(index, direction) {
  const next = index + direction;
  if (next < 0 || next >= state.route.length) return;
  [state.route[index], state.route[next]] = [state.route[next], state.route[index]];
  renderRoute();
  announce("Route order updated.");
}

function changeDays(index, amount) {
  const entry = state.route[index];
  if (!entry) return;
  const next = entry.days + amount;
  if (next < 1 || next > LIMITS.daysPerCity || totalDays() + amount > LIMITS.totalDays) return;
  entry.days = next;
  renderRoute();
  announce(`${cityFor(entry.city_id).name}: ${entry.days} days.`);
}

function selectAge(ageGroup) {
  state.ageGroup = ageGroup;
  document.querySelectorAll("[data-age]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.age === ageGroup));
  });
  updateTripValidation();
  announce(`${ageGroup[0].toUpperCase()}${ageGroup.slice(1)} pace selected.`);
}

function showStep(number) {
  for (let step = 1; step <= 3; step += 1) {
    byId(`step-${step === 1 ? "trip" : step === 2 ? "interests" : "itinerary"}`).hidden = step !== number;
    const indicator = document.querySelector(`[data-step-indicator="${step}"]`);
    indicator.classList.toggle("is-current", step === number);
    indicator.classList.toggle("is-complete", step < number);
    if (step === number) indicator.setAttribute("aria-current", "step");
    else indicator.removeAttribute("aria-current");
  }
  announce(`Step ${number} of 3.`);
  const prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" });

  const headingId = number === 1 ? "trip-title" : number === 2 ? "interests-title" : "itinerary-title";
  const heading = byId(headingId);
  if (heading) {
    heading.focus();
  }
}

async function loadCities() {
  try {
    const response = await fetch("/api/cities");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load cities.");
    state.cities = data;
    renderCities();
    renderRoute();
  } catch (error) {
    byId("city-list").replaceChildren(make("p", "error-message", "Could not reach the planner. Start the local server and reload this page."));
    byId("trip-validation").textContent = "The local planner is unavailable.";
    announce(error.message);
  }
}

function renderBubbles() {
  const pool = byId("bubble-pool");
  pool.replaceChildren();
  if (!state.categories.length) {
    pool.append(make("p", "empty-hint", "No interests are listed for these cities. You can continue without choosing any."));
  }
  for (const category of state.categories) {
    const selected = state.interests.has(category.id);
    const tier = category.count >= 4 ? "bubble-large" : category.count >= 2 ? "bubble-medium" : "bubble-small";
    const button = make("button", `interest-bubble ${tier}`);
    button.type = "button";
    button.setAttribute("aria-pressed", String(selected));
    button.setAttribute("aria-label", `${category.label}, ${category.count} places`);
    const label = make("span", "", category.label);
    const count = make("span", "bubble-count", String(category.count));
    const check = make("span", "bubble-check", "✓");
    check.setAttribute("aria-hidden", "true");
    button.append(label, count, check);
    button.addEventListener("click", () => toggleInterest(category.id, button));
    pool.append(button);
  }
  updateInterestCount();
}

function toggleInterest(id, button) {
  const category = state.categories.find((item) => item.id === id);
  if (state.interests.has(id)) state.interests.delete(id);
  else state.interests.add(id);
  const selected = state.interests.has(id);
  button.setAttribute("aria-pressed", String(selected));
  updateInterestCount();
  announce(`${category.label} ${selected ? "selected" : "removed"}.`);
}

function updateInterestCount() {
  const count = state.interests.size;
  byId("interest-count").textContent = `${count} selected`;
  byId("interests-skip").textContent = count ? "Skip interests" : "Skip";
}

async function loadCategories() {
  byId("interest-error").hidden = true;
  byId("bubble-pool").replaceChildren(make("p", "loading-line", "Finding interests along your route…"));
  showStep(2);
  const cityIds = state.route.map((entry) => entry.city_id).join(",");
  try {
    const response = await fetch(`/api/categories?cities=${encodeURIComponent(cityIds)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load interests.");
    state.categories = data;
    const visibleIds = new Set(data.map((item) => item.id));
    state.interests = new Set([...state.interests].filter((id) => visibleIds.has(id)));
    renderBubbles();
  } catch (error) {
    byId("interest-error").textContent = `${error.message} Go back and try again.`;
    byId("interest-error").hidden = false;
    byId("bubble-pool").replaceChildren();
  }
}

function addTag(list, label) {
  list.append(make("span", "stop-tag", label));
}

function renderPlan(plan) {
  const daysElement = byId("itinerary-days");
  daysElement.replaceChildren();
  byId("trip-summary").replaceChildren();

  const summary = [
    `${plan.profile.route.length} ${plan.profile.route.length === 1 ? "city" : "cities"}`,
    `${plan.days.length} ${plan.days.length === 1 ? "day" : "days"}`,
    `${plan.profile.age_group} pace`,
  ];
  for (const text of summary) byId("trip-summary").append(make("span", "summary-chip", text));
  for (const id of plan.profile.interests) {
    const category = state.categories.find((item) => item.id === id);
    if (category) byId("trip-summary").append(make("span", "summary-chip", category.label));
  }
  byId("trip-summary").hidden = false;

  byId("unverified-banner").textContent = plan.verified_data
    ? "Place details are marked as verified by the dataset owner. Check current opening information before travelling."
    : "Place details are unverified planning estimates. Check current opening hours and locations before travelling.";
  byId("unverified-banner").hidden = false;

  let currentCityId = null;
  let currentGroup = null;
  let currentDaysContainer = null;

  for (const day of plan.days) {
    if (day.city_id !== currentCityId) {
      currentCityId = day.city_id;

      if (day.transfer) {
        daysElement.append(make("div", "transfer-row",
          `Transfer · ${day.transfer.from} to ${day.transfer.to} · ${Math.round(day.transfer.km)} km · about ${formatDuration(day.transfer.minutes)}`));
      }

      currentGroup = make("section", "city-group");
      currentGroup.setAttribute("aria-label", `${day.city_name} itinerary`);

      const cityDaysCount = plan.days.filter((d) => d.city_id === day.city_id).length;
      const groupHeading = make("div", "city-group-heading");
      groupHeading.append(make("h3", "", day.city_name));
      groupHeading.append(make("span", "city-group-meta", `${cityDaysCount} ${cityDaysCount === 1 ? "day" : "days"}`));
      currentGroup.append(groupHeading);

      currentDaysContainer = make("div", "city-days");
      currentGroup.append(currentDaysContainer);
      daysElement.append(currentGroup);
    }

    const card = make("article", "day-card");
    const heading = make("div", "day-card-heading");
    const headingText = make("div");
    headingText.append(make("h3", "", `Day ${day.day} · ${day.city_name}`));
    headingText.append(make("p", "", `${day.start} – ${day.end}`));
    heading.append(headingText, make("span", "day-value", `Value ${day.value}`));
    card.append(heading);

    if (day.approximate) {
      card.append(make("p", "approximate-note", "This day is approximate because the candidate limit was reached."));
    }
    if (!day.stops.length) {
      card.append(make("p", "empty-day", "No places fit this day. The next day is still planned."));
    } else {
      const stops = make("ol", "stop-list");
      for (const stop of day.stops) {
        const row = make("li", "stop-row");
        row.append(make("span", "stop-time", stop.start));
        const info = make("div");
        info.append(make("span", "stop-name", stop.name));
        const detail = [stop.area, `${stop.duration_min} min`].filter(Boolean).join(" · ");
        info.append(make("span", "stop-detail", detail));
        const tags = make("span", "tag-list");
        if (stop.souvenir >= 3) addTag(tags, "Souvenirs");
        if (stop.day_trip) addTag(tags, "Day trip");
        if (stop.matches_interest) addTag(tags, "Matches your interests");
        if (tags.childElementCount) info.append(tags);
        row.append(info);
        stops.append(row);
      }
      card.append(stops);
    }
    currentDaysContainer.append(card);
  }

  const placeCount = plan.days.reduce((count, day) => count + day.stops.length, 0);
  const total = byId("plan-total");
  total.replaceChildren(
    make("span", "", `${placeCount} places across ${plan.days.length} days`),
    make("strong", "", `Total value ${plan.total_value}`),
  );
  total.hidden = false;
}

function formatDuration(minutes) {
  const rounded = Math.round(minutes);
  const hours = Math.floor(rounded / 60);
  const remainder = rounded % 60;
  if (hours && remainder) return `${hours}h ${remainder}m`;
  if (hours) return `${hours}h`;
  return `${remainder}m`;
}

async function buildPlan() {
  showStep(3);
  byId("plan-error").hidden = true;
  byId("itinerary-days").replaceChildren();
  byId("trip-summary").hidden = true;
  byId("plan-total").hidden = true;
  byId("unverified-banner").hidden = true;
  byId("plan-loading").hidden = false;
  try {
    const response = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        age_group: state.ageGroup,
        route: state.route,
        interests: [...state.interests],
        algorithm: "astar",
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The planner could not build this itinerary.");
    state.plan = result;
    renderPlan(result);
  } catch (error) {
    const isNetwork = error instanceof TypeError || error.message.includes("fetch");
    byId("plan-error").textContent = isNetwork
      ? `${error.message}. Check that the local planner is running, then try again.`
      : error.message;
    byId("plan-error").hidden = false;
    announce(error.message);
  } finally {
    byId("plan-loading").hidden = true;
  }
}

function resetToTrip() {
  showStep(1);
  announce("Edit your route and plan another trip.");
}

document.querySelectorAll("[data-age]").forEach((button) => {
  button.addEventListener("click", () => selectAge(button.dataset.age));
});
byId("trip-continue").addEventListener("click", loadCategories);
byId("interests-back").addEventListener("click", () => showStep(1));
byId("interests-clear").addEventListener("click", () => {
  state.interests.clear();
  renderBubbles();
  announce("Interest choices cleared.");
});
byId("interests-skip").addEventListener("click", () => {
  state.interests.clear();
  buildPlan();
});
byId("interests-continue").addEventListener("click", buildPlan);
byId("itinerary-back").addEventListener("click", () => showStep(2));
byId("plan-again").addEventListener("click", resetToTrip);
byId("plan-again-bottom").addEventListener("click", resetToTrip);

loadCities();
