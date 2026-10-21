/* Enhancement only: generated links and book content work without JavaScript. */
(() => {
  "use strict";

  const html = document.documentElement;
  const body = document.body;
  if (!body) return;

  let rootUrl;
  try {
    rootUrl = new URL(body.dataset.root || "./", window.location.href);
    if (rootUrl.origin !== window.location.origin) return;
    if (!rootUrl.pathname.endsWith("/")) rootUrl.pathname += "/";
  } catch {
    return;
  }

  const storagePrefix = `pi-beginner-book:${rootUrl.pathname}:`;
  const readSetting = (key) => {
    try {
      return window.localStorage.getItem(storagePrefix + key);
    } catch {
      return null;
    }
  };
  const writeSetting = (key, value) => {
    try {
      window.localStorage.setItem(storagePrefix + key, value);
    } catch {
      // Private browsing and storage policies can disable persistence.
    }
  };

  const themeButton = document.getElementById("theme-toggle");
  const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
  let chosenTheme = readSetting("theme");
  if (chosenTheme !== "light" && chosenTheme !== "dark") chosenTheme = null;

  const applyTheme = (theme) => {
    html.dataset.theme = theme;
    if (!themeButton) return;
    const dark = theme === "dark";
    themeButton.textContent = dark ? "切换浅色" : "切换深色";
    themeButton.setAttribute("aria-label", dark ? "切换到浅色主题" : "切换到深色主题");
    themeButton.setAttribute("aria-pressed", String(dark));
  };
  applyTheme(chosenTheme || (systemTheme.matches ? "dark" : "light"));
  if (themeButton) {
    themeButton.hidden = false;
    themeButton.addEventListener("click", () => {
      chosenTheme = html.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(chosenTheme);
      writeSetting("theme", chosenTheme);
    });
  }
  const handleSystemTheme = (event) => {
    if (!chosenTheme) applyTheme(event.matches ? "dark" : "light");
  };
  if (typeof systemTheme.addEventListener === "function") {
    systemTheme.addEventListener("change", handleSystemTheme);
  }

  const minimumSize = 16;
  const maximumSize = 24;
  const decreaseButton = document.getElementById("font-decrease");
  const increaseButton = document.getElementById("font-increase");
  const storedSize = Number(readSetting("reading-size"));
  let readingSize = Number.isInteger(storedSize) && storedSize >= minimumSize && storedSize <= maximumSize ? storedSize : 18;
  const applyReadingSize = () => {
    html.style.setProperty("--reading-size", `${readingSize}px`);
    if (decreaseButton) decreaseButton.disabled = readingSize <= minimumSize;
    if (increaseButton) increaseButton.disabled = readingSize >= maximumSize;
  };
  applyReadingSize();
  if (decreaseButton && increaseButton) {
    decreaseButton.hidden = false;
    increaseButton.hidden = false;
    decreaseButton.setAttribute("aria-label", "减小正文字号");
    increaseButton.setAttribute("aria-label", "增大正文字号");
    decreaseButton.textContent = "A−";
    increaseButton.textContent = "A+";
    decreaseButton.addEventListener("click", () => {
      readingSize = Math.max(minimumSize, readingSize - 1);
      applyReadingSize();
      writeSetting("reading-size", String(readingSize));
    });
    increaseButton.addEventListener("click", () => {
      readingSize = Math.min(maximumSize, readingSize + 1);
      applyReadingSize();
      writeSetting("reading-size", String(readingSize));
    });
  }

  const menuButton = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("book-nav");
  const mobileLayout = window.matchMedia("(max-width: 900px)");
  if (menuButton && sidebar) {
    const setMenuOpen = (open, restoreFocus = false) => {
      const expanded = Boolean(open && mobileLayout.matches);
      body.classList.toggle("nav-open", expanded);
      menuButton.setAttribute("aria-expanded", String(expanded));
      menuButton.textContent = expanded ? "关闭目录" : "目录";
      menuButton.setAttribute("aria-label", expanded ? "关闭章节目录" : "打开章节目录");
      if (!expanded && restoreFocus) menuButton.focus();
    };
    menuButton.hidden = false;
    menuButton.addEventListener("click", () => {
      setMenuOpen(menuButton.getAttribute("aria-expanded") !== "true");
    });
    sidebar.addEventListener("click", (event) => {
      const target = event.target;
      if (target instanceof Element && target.closest("a")) setMenuOpen(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && body.classList.contains("nav-open")) {
        setMenuOpen(false, true);
        event.preventDefault();
      }
    });
    if (typeof mobileLayout.addEventListener === "function") {
      mobileLayout.addEventListener("change", () => setMenuOpen(false));
    }
    setMenuOpen(false);
    html.classList.add("nav-enhanced");
  }

  const chapterPattern = /^chapters\/[a-z0-9][a-z0-9-]*\.html$/;
  const knownChapters = new Set();
  const chapterLinks = document.querySelectorAll(".chapter-list a[href]");
  for (const link of chapterLinks) {
    try {
      const url = new URL(link.href, window.location.href);
      if (url.origin !== rootUrl.origin || !url.pathname.startsWith(rootUrl.pathname)) continue;
      const page = url.pathname.slice(rootUrl.pathname.length);
      if (chapterPattern.test(page)) knownChapters.add(page);
    } catch {
      // A malformed navigation item must not prevent the rest of the page from working.
    }
  }

  const getChapterUrl = (page, hash) => {
    if (typeof page !== "string" || !chapterPattern.test(page)) return null;
    if (knownChapters.size === 0 || !knownChapters.has(page)) return null;
    if (typeof hash !== "string" || hash.length > 2048 || (hash !== "" && !hash.startsWith("#"))) return null;
    try {
      const url = new URL(page, rootUrl);
      if (url.origin !== window.location.origin || url.pathname !== rootUrl.pathname + page) return null;
      url.hash = hash;
      return url;
    } catch {
      return null;
    }
  };

  const resumeLink = document.getElementById("resume-reading");
  if (resumeLink) {
    try {
      const saved = JSON.parse(readSetting("last-chapter") || "null");
      if (saved && typeof saved === "object" && !Array.isArray(saved)) {
        const url = getChapterUrl(saved.page, saved.hash);
        if (url && typeof saved.title === "string" && saved.title.length > 0 && saved.title.length <= 200) {
          // Use a relative link so GitHub Pages project paths and local previews both work.
          resumeLink.setAttribute("href", `${body.dataset.root || "./"}${saved.page}${url.hash}`);
          resumeLink.setAttribute("aria-label", `继续阅读：${saved.title}`);
          resumeLink.title = saved.title;
          resumeLink.hidden = false;
        }
      }
    } catch {
      // Invalid or inaccessible saved state leaves the ordinary start-reading link intact.
    }
  }

  const currentPage = body.dataset.page;
  if (body.classList.contains("reader") && getChapterUrl(currentPage, window.location.hash)) {
    const saveChapter = () => {
      const hash = window.location.hash;
      const title = (body.dataset.title || document.title || "").trim().slice(0, 200);
      if (!title || !getChapterUrl(currentPage, hash)) return;
      writeSetting("last-chapter", JSON.stringify({ page: currentPage, title, hash }));
    };
    saveChapter();
    window.addEventListener("hashchange", saveChapter);
    window.addEventListener("pagehide", saveChapter);
  }
})();
