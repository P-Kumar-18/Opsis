// ============================================
// Opsis — frontend interactions
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  const inits = [
    initMobileNav,
    initSegmentedTabs,
    initRecommendForms,
    initScrollReveal,
    initCountUp,
    fillScoreRings,
  ];
  inits.forEach((fn) => {
    try {
      fn();
    } catch (err) {
      console.error(`Opsis: ${fn.name} failed to initialize`, err);
    }
  });

  setTimeout(() => {
    document
      .querySelectorAll(".reveal, .reveal-group, .thread-divider, .hero-demo")
      .forEach((el) => el.classList.add("is-visible"));
  }, 2500);
});


// --------------------------------------------
// Mobile nav toggle
// --------------------------------------------

function initMobileNav() {
  const toggle = document.getElementById("navToggle");
  const mobileNav = document.getElementById("mobileNav");

  if (!toggle || !mobileNav) return;

  toggle.addEventListener("click", () => {
    const isOpen = mobileNav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}


// --------------------------------------------
// Scroll-reveal system
// --------------------------------------------

let _revealObserver = null;

function getRevealObserver() {
  if (_revealObserver) return _revealObserver;
  if (!("IntersectionObserver" in window)) return null;

  _revealObserver = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
  );

  return _revealObserver;
}

function observeReveal(el) {
  const observer = getRevealObserver();
  if (!observer) {
    el.classList.add("is-visible");
    return;
  }
  observer.observe(el);
}

function initScrollReveal() {
  document
    .querySelectorAll(".reveal, .reveal-group, .thread-divider, .hero-demo")
    .forEach(observeReveal);
}


// --------------------------------------------
// Count-up numbers
// --------------------------------------------

function prefersReducedMotion() {
  return (
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function startCount(el) {
  const target = parseInt(el.dataset.count, 10);
  if (Number.isNaN(target)) return;

  if (prefersReducedMotion()) {
    el.textContent = target.toLocaleString("en-US");
    return;
  }

  const duration = 900;
  const startTime = performance.now();

  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * eased).toLocaleString("en-US");
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function observeCount(el) {
  if (!("IntersectionObserver" in window)) {
    startCount(el);
    return;
  }
  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          startCount(entry.target);
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.4 }
  );
  observer.observe(el);
}

function initCountUp(root = document) {
  root.querySelectorAll("[data-count]").forEach(observeCount);
}


// --------------------------------------------
// Score ring fill
// --------------------------------------------

function fillScoreRings(root = document) {
  const rings = root.querySelectorAll(".score-ring-fg:not(.is-filled)");
  if (!rings.length) return;
  requestAnimationFrame(() => {
    setTimeout(() => {
      rings.forEach((ring) => ring.classList.add("is-filled"));
    }, 50);
  });
}


// --------------------------------------------
// Segmented input tabs
// --------------------------------------------

function initSegmentedTabs() {
  const segmented = document.querySelector(".segmented");
  const indicator = document.querySelector(".segment-indicator");
  const segments = document.querySelectorAll(".segment");

  if (!segments.length) return;

  function moveIndicatorTo(segment) {
    if (!indicator || !segmented || !segment) return;
    const segRect = segment.getBoundingClientRect();
    const parentRect = segmented.getBoundingClientRect();
    indicator.style.width = `${segRect.width}px`;
    indicator.style.transform = `translateX(${segRect.left - parentRect.left}px)`;
  }

  function setActiveForm(targetId) {
    document.querySelectorAll(".input-form").forEach((form) => {
      const isTarget = form.getAttribute("data-panel") === targetId;
      if (isTarget) {
        form.removeAttribute("hidden");
        form.style.display = "block";
      } else {
        form.setAttribute("hidden", "true");
        form.style.display = "none";
      }
    });
  }

  segments.forEach((segment) => {
    segment.addEventListener("click", () => {
      segments.forEach((s) => {
        s.classList.remove("active");
        s.setAttribute("aria-selected", "false");
      });

      segment.classList.add("active");
      segment.setAttribute("aria-selected", "true");
      moveIndicatorTo(segment);
      
      setActiveForm(segment.getAttribute("data-target"));
    });
  });

  const initialSegment =
    document.querySelector(".segment.active") || segments[0];

  setActiveForm(initialSegment.getAttribute("data-target"));

  if (indicator) {
    indicator.style.transition = "none";
    moveIndicatorTo(initialSegment);
    requestAnimationFrame(() => {
      indicator.style.transition = "";
    });
  }

  window.addEventListener("resize", () => {
    const current = document.querySelector(".segment.active") || segments[0];
    moveIndicatorTo(current);
  });
}


// --------------------------------------------
// Recommend form
// --------------------------------------------

const LOADING_STAGES = [
  { text: "Searching the archive…", at: 0 },
  { text: "Fetching the fic's details…", at: 3000 },
  { text: "Comparing summaries and tags…", at: 7000 },
  { text: "Lining up what's closest…", at: 12000 },
  { text: "Almost there…", at: 17000 },
];

function initRecommendForms() {
  const forms = document.querySelectorAll(".input-form");
  if (!forms.length) return;

  forms.forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(form);
      const payload = {};

      formData.forEach((value, key) => {
        if (value.trim() !== "") {
          payload[key] = value.trim();
        }
      });

      if (Object.keys(payload).length === 0) {
        const visibleInput = form.querySelector('input:not([type="hidden"])');
        if (visibleInput) {
          visibleInput.focus();
        }
        return; 
      }

      await runRecommendation(payload);
    });
  });
}


// --------------------------------------------
// Run recommendation
// --------------------------------------------

async function runRecommendation(payload) {
  const submitButtons = document.querySelectorAll(
    ".input-form button[type='submit']"
  );
  const loadingSection = document.getElementById("loadingSection");
  const loadingMessage = document.getElementById("loadingMessage");
  const resultsSection = document.getElementById("resultsSection");
  const emptyState = document.getElementById("emptyState");
  
  const sourceBlock = document.getElementById("sourceBlock");
  const recsGrid = document.getElementById("recsGrid");

  if (sourceBlock) sourceBlock.innerHTML = "";
  if (recsGrid) recsGrid.innerHTML = "";

  submitButtons.forEach((btn) => (btn.disabled = true));
  if (resultsSection) resultsSection.hidden = true;
  if (emptyState) emptyState.hidden = true;
  if (loadingSection) loadingSection.hidden = false;

  const dots = document.querySelectorAll("#loadingDots .loading-dot");
  dots.forEach((dot, dotIndex) =>
    dot.classList.toggle("active", dotIndex === 0)
  );

  const timers = LOADING_STAGES.map((stage, index) =>
    setTimeout(() => {
      if (loadingMessage) {
        loadingMessage.style.opacity = 0;
        setTimeout(() => {
          loadingMessage.textContent = stage.text;
          loadingMessage.style.opacity = 1;
        }, 180);
      }
      dots.forEach((dot, dotIndex) =>
        dot.classList.toggle("active", dotIndex <= index)
      );
    }, stage.at)
  );

  try {
    const response = await fetch("/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    timers.forEach(clearTimeout);

    if (data.source && data.recommendations) {
      renderResults(data.source, data.recommendations);
    } else {
      renderError(data.error);
    }
  } catch (err) {
    timers.forEach(clearTimeout);
    renderError();
  } finally {
    submitButtons.forEach((btn) => (btn.disabled = false));
    if (loadingSection) loadingSection.hidden = true;
    if (loadingMessage) loadingMessage.textContent = LOADING_STAGES[0].text;
  }
}


// --------------------------------------------
// Render recommendation results
// --------------------------------------------

function renderResults(source, recommendations) {
  const resultsSection = document.getElementById("resultsSection");
  const sourceBlock = document.getElementById("sourceBlock");
  const recsGrid = document.getElementById("recsGrid");

  if (!resultsSection || !sourceBlock || !recsGrid) return;

  sourceBlock.innerHTML = `
    <div class="source-eyebrow-row">
      <p class="eyebrow">Because you liked this</p>
      ${
        source.newly_indexed
          ? `<span class="badge-new">Freshly indexed — just fetched from AO3</span>`
          : ""
      }
    </div>

    <div class="source-card">
      <div class="source-main">
        <h2 class="source-title">${escapeHtml(source.name)}</h2>
        <p class="source-author">by ${escapeHtml(source.author)}</p>
        <p class="source-summary">${escapeHtml(source.summary || "")}</p>
        <div class="source-tags">
          ${(source.fandoms || [])
            .map((f) => `<span class="tag">${escapeHtml(f)}</span>`)
            .join("")}
          ${(source.relationships || [])
            .map((r) => `<span class="tag tag-rel">${escapeHtml(r)}</span>`)
            .join("")}
        </div>
      </div>

      <div class="source-stats">
        <div class="stat">
          <span class="stat-value" data-count="${Number(source.hits) || 0}">0</span>
          <span class="stat-label">Hits</span>
        </div>
        <div class="stat">
          <span class="stat-value" data-count="${Number(source.kudos) || 0}">0</span>
          <span class="stat-label">Kudos</span>
        </div>
        <div class="stat">
          <span class="stat-value" data-count="${Number(source.bookmarks) || 0}">0</span>
          <span class="stat-label">Bookmarks</span>
        </div>
        <div class="stat">
          <span class="stat-value">${source.chapters}</span>
          <span class="stat-label">Chapters</span>
        </div>
        <div class="stat">
          <span class="stat-value" data-count="${Number(source.words) || 0}">0</span>
          <span class="stat-label">Words</span>
        </div>
      </div>

      <a href="${escapeAttr(source.url)}" target="_blank" rel="noopener" class="btn btn-ghost btn-small source-link">
        Read on AO3 ↗
      </a>
    </div>
  `;

  recsGrid.innerHTML = recommendations.map(renderRecCard).join("");

  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  initCountUp(sourceBlock);
  initCountUp(recsGrid);
  fillScoreRings(recsGrid);
}


// --------------------------------------------
// Render recommendation card
// --------------------------------------------

function getScoreTier(score) {
  if (score >= 0.85) return "high";
  if (score >= 0.6) return "mid";
  return "low";
}

function formatStatusLabel(status) {
  if (!status) return "";
  return String(status)
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderRecCard(rec) {
  const score = rec.score || 0;
  const pct = Math.round(score);
  const tier = getScoreTier(score);

  const resolvedStatus = (rec.status && rec.status !== "-") ? rec.status : "Completed";
  const statusSlug = resolvedStatus.toLowerCase().replace(/\s+/g, "-");
  const statusClass = `status-${statusSlug}`;
  const statusLabel = formatStatusLabel(resolvedStatus);

  return `
    <article class="rec-card" data-tier="${tier}">
      <div class="rec-explanation" aria-hidden="true">
        <span class="rec-explanation-label">Why this match</span>
        <p>${escapeHtml(rec.explanation || "Explanation unavailable.")}</p>
      </div>
      <div class="rec-card-head">
        <div>
          <h3 class="rec-title">${escapeHtml(rec.name)}</h3>
          <p class="rec-author">by ${escapeHtml(rec.author)}</p>
        </div>

        <div class="score-meter" aria-label="${pct} percent match">
          <svg viewBox="0 0 40 40" class="score-ring">
            <circle cx="20" cy="20" r="17" class="score-ring-bg" />
            <circle cx="20" cy="20" r="17" class="score-ring-fg" style="--pct: ${score / 100}" />
          </svg>
          <span class="score-value">
            <span class="count-num" data-count="${pct}">0</span><span class="score-unit">%</span>
          </span>
        </div>
      </div>

      <div class="rec-tags">
        ${(rec.fandoms || [])
          .map((f) => `<span class="tag">${escapeHtml(f)}</span>`)
          .join("")}
      </div>

      ${
        rec.relationships && rec.relationships.length
          ? `<p class="rec-relationships">${rec.relationships
              .map(escapeHtml)
              .join(" · ")}</p>`
          : ""
      }

      <div class="rec-meta">
        <span>${formatNumber(rec.words)} words</span>
        <span class="dot">·</span>
        <span>${rec.chapters} ch</span>
        <span class="dot">·</span>
        <span class="status-badge ${statusClass}">${escapeHtml(statusLabel)}</span>
      </div>

      <div class="rec-footer">
        <div class="rec-signals">
          <span>${formatNumber(rec.hits)} hits</span>
          <span>${formatNumber(rec.kudos)} kudos</span>
          <span>${formatNumber(rec.bookmarks)} bookmarks</span>
        </div>

        <a href="${escapeAttr(rec.url)}" target="_blank" rel="noopener" class="rec-link">
          Read ↗
        </a>
      </div>
    </article>
  `;
}


// --------------------------------------------
// Error handling
// --------------------------------------------

function renderError(message) {
  const emptyState = document.getElementById("emptyState");
  if (!emptyState) return;

  emptyState.querySelector("p").textContent =
    message ||
    "That fic couldn't be found or reached. Double-check the ID, link, or title and try again.";

  emptyState.hidden = false;
  emptyState.scrollIntoView({ behavior: "smooth", block: "start" });
}


// --------------------------------------------
// Helpers
// --------------------------------------------

function formatNumber(n) {
  if (n === undefined || n === null) return "—";
  return Number(n).toLocaleString("en-US");
}

function escapeHtml(str) {
  if (str === undefined || str === null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttr(str) {
  return escapeHtml(str);
}