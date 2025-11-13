const LANG_STORAGE_KEY = 'mc-news-lang';
const SECTION_CONFIG = [
  {
    tag: 'creators',
    anchor: 'creators',
    heading: {
      pl: 'Twórcy generatywnej AI',
      en: 'Generative AI creators',
    },
  },
  {
    tag: 'marketing',
    anchor: 'marketing',
    heading: {
      pl: 'Marketing i rozrywka',
      en: 'Marketing & entertainment',
    },
  },
  {
    tag: 'bizdev',
    anchor: 'bizdev',
    heading: {
      pl: 'Biznes i rozwój',
      en: 'Business & development',
    },
  },
];

const state = {
  lang: 'pl',
  articles: [],
};

const PLACEHOLDER_IMAGE =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%230f172a"/><stop offset="100%" stop-color="%231e293b"/></linearGradient></defs><rect width="800" height="500" fill="url(%23grad)"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial,sans-serif" font-size="36" fill="white" opacity="0.7">AI News</text></svg>';

function ensureString(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function getLocalizedField(article, key) {
  const base = ensureString(article?.[key]);
  const pl = ensureString(article?.[`${key}_pl`]) || ensureString(article?.[`${key}Pl`]);
  const en = ensureString(article?.[`${key}_en`]) || ensureString(article?.[`${key}En`]);
  const fallback = base || en || pl;
  return {
    pl: pl || fallback,
    en: en || fallback,
  };
}

function resolveSource(article) {
  const source = ensureString(article?.source) || ensureString(article?.provider) || ensureString(article?.providerName);
  if (source) {
    return source;
  }
  try {
    const url = new URL(article?.url ?? '');
    return url.hostname.replace(/^www\./, '');
  } catch (err) {
    return 'Source';
  }
}

function resolveImage(article) {
  const url = ensureString(article?.imageUrl) || ensureString(article?.image);
  return url || PLACEHOLDER_IMAGE;
}

const heroContainer = document.getElementById('hero');
const latestContainer = document.getElementById('latest');
const sectionsContainer = document.getElementById('sections');
const bannerPl = document.querySelector('[data-role="banner-pl"]');
const bannerEn = document.querySelector('[data-role="banner-en"]');
const langButtons = Array.from(document.querySelectorAll('.lang-button'));

function applyLanguage(lang) {
  const target = lang === 'en' ? 'en' : 'pl';
  state.lang = target;
  document.documentElement.setAttribute('lang', target);
  document.body.classList.remove('lang-pl', 'lang-en');
  document.body.classList.add(`lang-${target}`);
  langButtons.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.lang === target);
  });
  try {
    localStorage.setItem(LANG_STORAGE_KEY, target);
  } catch (err) {
    console.warn('Unable to persist language preference', err);
  }
}

function initLanguageToggle() {
  langButtons.forEach((btn) => {
    btn.addEventListener('click', () => applyLanguage(btn.dataset.lang || 'pl'));
  });
  let preferred = 'pl';
  try {
    const stored = localStorage.getItem(LANG_STORAGE_KEY);
    if (stored === 'pl' || stored === 'en') {
      preferred = stored;
    }
  } catch (err) {
    preferred = 'pl';
  }
  applyLanguage(preferred);
}

function createLangElements(tag, texts, { className, attrs } = {}) {
  const fragment = document.createDocumentFragment();
  const attrResolver = typeof attrs === 'function' ? attrs : () => attrs || {};
  Object.entries(texts).forEach(([lang, text]) => {
    const el = document.createElement(tag);
    el.dataset.langContent = lang;
    if (className) {
      if (Array.isArray(className)) {
        el.classList.add(...className);
      } else {
        el.className = className;
      }
    }
    const resolvedAttrs = attrResolver(lang) || {};
    Object.entries(resolvedAttrs).forEach(([attr, value]) => {
      if (value !== undefined && value !== null) {
        el.setAttribute(attr, value);
      }
    });
    if (text !== undefined && text !== null) {
      el.textContent = String(text);
    } else {
      el.textContent = '';
    }
    fragment.appendChild(el);
  });
  return fragment;
}

function formatDate(value, lang) {
  const locale = lang === 'en' ? 'en-GB' : 'pl-PL';
  const date = new Date(value);
  const datePart = new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    timeZone: 'Europe/Warsaw',
  }).format(date);
  const timePart = new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Europe/Warsaw',
  }).format(date);
  return `${datePart}, ${timePart}`;
}

function formatBannerDate(date, lang, timeZone) {
  const locale = lang === 'en' ? 'en-GB' : 'pl-PL';
  const dayPart = new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone,
  }).format(date);
  const timePart = new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone,
  }).format(date);
  return `${dayPart}, ${timePart}`;
}

function hasTag(article, tag) {
  return Array.isArray(article.tags) && article.tags.includes(tag);
}

function renderHero(articles) {
  heroContainer.innerHTML = '';
  const heroArticle = articles.find((item) => hasTag(item, 'hero')) || articles[0];
  if (!heroArticle) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.appendChild(
      createLangElements('span', {
        pl: 'Brak artykułów do wyświetlenia.',
        en: 'No stories to display.',
      }),
    );
    heroContainer.appendChild(empty);
    return;
  }

  const articleEl = document.createElement('article');
  articleEl.className = 'hero-article';

  const imageLink = document.createElement('a');
  imageLink.className = 'hero-image';
  imageLink.href = heroArticle.url;
  imageLink.target = '_blank';
  imageLink.rel = 'noopener';
  const img = document.createElement('img');
  img.src = resolveImage(heroArticle);
  img.alt = ensureString(heroArticle.title) || 'AI News illustration';
  img.loading = 'lazy';
  imageLink.appendChild(img);
  articleEl.appendChild(imageLink);

  const content = document.createElement('div');
  content.className = 'hero-content';
  content.appendChild(
    createLangElements('span', {
      pl: 'Najważniejszy temat',
      en: 'Top story',
    }, { className: 'pill' }),
  );

  const title = document.createElement('h2');
  const heroTitle = getLocalizedField(heroArticle, 'title');
  title.appendChild(
    createLangElements(
      'a',
      heroTitle,
      {
        attrs: {
          href: heroArticle.url,
          target: '_blank',
          rel: 'noopener',
        },
      },
    ),
  );
  content.appendChild(title);

  const meta = document.createElement('p');
  meta.className = 'meta';
  const heroSource = resolveSource(heroArticle);
  meta.appendChild(
    createLangElements('span', {
      pl: `${heroSource} • ${formatDate(heroArticle.publishedAt, 'pl')}`,
      en: `${heroSource} • ${formatDate(heroArticle.publishedAt, 'en')}`,
    }),
  );
  content.appendChild(meta);

  const heroSummary = getLocalizedField(heroArticle, 'summary');
  if (heroSummary.pl || heroSummary.en) {
    const summary = document.createElement('p');
    summary.className = 'summary';
    summary.appendChild(createLangElements('span', heroSummary));
    content.appendChild(summary);
  }

  const ctaWrap = document.createElement('div');
  ctaWrap.className = 'hero-cta';
  ctaWrap.appendChild(
    createLangElements(
      'a',
      {
        pl: 'Czytaj artykuł →',
        en: 'Read article →',
      },
      {
        className: 'hero-button',
        attrs: {
          href: heroArticle.url,
          target: '_blank',
          rel: 'noopener',
        },
      },
    ),
  );
  content.appendChild(ctaWrap);

  articleEl.appendChild(content);
  heroContainer.appendChild(articleEl);
}

function buildLatestList(articles, heroArticle) {
  const usedUrls = new Set();
  if (heroArticle?.url) {
    usedUrls.add(heroArticle.url);
  }
  const latest = [];
  articles.forEach((article) => {
    if (latest.length >= 6) {
      return;
    }
    if (!article.url || usedUrls.has(article.url)) {
      return;
    }
    if (hasTag(article, 'brief')) {
      latest.push(article);
      usedUrls.add(article.url);
    }
  });

  if (latest.length < 6) {
    articles.forEach((article) => {
      if (latest.length >= 6) {
        return;
      }
      if (!article.url || usedUrls.has(article.url)) {
        return;
      }
      latest.push(article);
      usedUrls.add(article.url);
    });
  }

  return latest;
}

function renderLatest(articles) {
  latestContainer.innerHTML = '';
  if (!articles.length) {
    return;
  }

  const heroArticle = articles.find((item) => hasTag(item, 'hero')) || articles[0];
  const latestArticles = buildLatestList(articles, heroArticle);
  if (!latestArticles.length) {
    return;
  }

  const heading = document.createElement('h3');
  heading.appendChild(
    createLangElements('span', {
      pl: 'W skrócie',
      en: 'In brief',
    }),
  );
  latestContainer.appendChild(heading);

  const list = document.createElement('ul');
  latestArticles.forEach((article) => {
    const item = document.createElement('li');
    const titleTexts = getLocalizedField(article, 'title');
    item.appendChild(
      createLangElements(
        'a',
        titleTexts,
        {
          attrs: {
            href: article.url,
            target: '_blank',
            rel: 'noopener',
          },
        },
      ),
    );
    const source = document.createElement('span');
    source.className = 'latest-source';
    const sourceLabel = resolveSource(article);
    source.appendChild(
      createLangElements('span', {
        pl: sourceLabel,
        en: sourceLabel,
      }),
    );
    item.appendChild(source);
    list.appendChild(item);
  });

  latestContainer.appendChild(list);
}

function renderSectionCards(tag, articles) {
  const grid = document.createElement('div');
  grid.className = 'news-grid';

  articles.forEach((article) => {
    const card = document.createElement('article');
    card.className = 'news-card';

    const imageLink = document.createElement('a');
    imageLink.className = 'card-image';
    imageLink.href = article.url;
    imageLink.target = '_blank';
    imageLink.rel = 'noopener';
    const img = document.createElement('img');
    img.src = resolveImage(article);
    img.alt = ensureString(article.title) || 'AI News illustration';
    img.loading = 'lazy';
    imageLink.appendChild(img);
    card.appendChild(imageLink);

    const body = document.createElement('div');
    body.className = 'card-body';

    const heading = document.createElement('h3');
    const titleTexts = getLocalizedField(article, 'title');
    heading.appendChild(
      createLangElements(
        'a',
        titleTexts,
        {
          attrs: {
            href: article.url,
            target: '_blank',
            rel: 'noopener',
          },
        },
      ),
    );
    body.appendChild(heading);

    const meta = document.createElement('p');
    meta.className = 'meta';
    const sourceLabel = resolveSource(article);
    meta.appendChild(
      createLangElements('span', {
        pl: `${sourceLabel} • ${formatDate(article.publishedAt, 'pl')}`,
        en: `${sourceLabel} • ${formatDate(article.publishedAt, 'en')}`,
      }),
    );
    body.appendChild(meta);

    const summaryTexts = getLocalizedField(article, 'summary');
    if (summaryTexts.pl || summaryTexts.en) {
      const summary = document.createElement('p');
      summary.className = 'summary';
      summary.appendChild(createLangElements('span', summaryTexts));
      body.appendChild(summary);
    }

    card.appendChild(body);
    grid.appendChild(card);
  });

  return grid;
}

function renderSections(articles) {
  sectionsContainer.innerHTML = '';
  SECTION_CONFIG.forEach((section) => {
    const sectionArticles = articles.filter((article) => hasTag(article, section.tag)).slice(0, N_PER_BUCKET);
    if (!sectionArticles.length) {
      return;
    }
    const wrapper = document.createElement('section');
    wrapper.className = 'section-block';
    wrapper.id = section.anchor;

    const header = document.createElement('header');
    header.className = 'section-header';
    const title = document.createElement('h2');
    title.appendChild(
      createLangElements('span', {
        pl: section.heading.pl,
        en: section.heading.en,
      }),
    );
    header.appendChild(title);
    wrapper.appendChild(header);

    wrapper.appendChild(renderSectionCards(section.tag, sectionArticles));
    sectionsContainer.appendChild(wrapper);
  });
}

function updateBanner(articles) {
  if (!bannerPl || !bannerEn) {
    return;
  }
  const timestamps = articles
    .map((article) => {
      const value = new Date(article.publishedAt).getTime();
      return Number.isFinite(value) ? value : null;
    })
    .filter((value) => value !== null);
  if (!timestamps.length) {
    return;
  }
  const latest = new Date(Math.max(...timestamps));
  bannerPl.textContent = `Aktualizacja: ${formatBannerDate(latest, 'pl', 'Europe/Warsaw')} (Warszawa) / ${formatBannerDate(
    latest,
    'pl',
    'America/Los_Angeles',
  )} (Los Angeles)`;
  bannerEn.textContent = `Updated: ${formatBannerDate(latest, 'en', 'Europe/Warsaw')} (Warsaw) / ${formatBannerDate(
    latest,
    'en',
    'America/Los_Angeles',
  )} (Los Angeles)`;
}

function showLoading() {
  heroContainer.innerHTML = '';
  const loading = document.createElement('p');
  loading.className = 'loading-state';
  loading.appendChild(
    createLangElements('span', {
      pl: 'Ładowanie najnowszych wiadomości…',
      en: 'Loading the latest headlines…',
    }),
  );
  heroContainer.appendChild(loading);
}

function showError() {
  heroContainer.innerHTML = '';
  const error = document.createElement('p');
  error.className = 'error-state';
  error.appendChild(
    createLangElements('span', {
      pl: 'Nie udało się pobrać wiadomości. Spróbuj ponownie później.',
      en: 'Failed to load the news feed. Please try again later.',
    }),
  );
  heroContainer.appendChild(error);
}

function renderAll() {
  const articles = state.articles;
  if (!Array.isArray(articles) || !articles.length) {
    renderHero([]);
    latestContainer.innerHTML = '';
    sectionsContainer.innerHTML = '';
    return;
  }
  renderHero(articles);
  renderLatest(articles);
  renderSections(articles);
  updateBanner(articles);
}

async function loadNews() {
  showLoading();
  try {
    const response = await fetch('data/news.json', {
      cache: 'no-cache',
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const payload = await response.json();
    const articles = Array.isArray(payload) ? payload : Array.isArray(payload.articles) ? payload.articles : [];
    state.articles = articles;
    renderAll();
  } catch (error) {
    console.error('Unable to load news.json', error);
    showError();
  }
}

const N_PER_BUCKET = 5;

document.addEventListener('DOMContentLoaded', () => {
  initLanguageToggle();
  loadNews();
});
