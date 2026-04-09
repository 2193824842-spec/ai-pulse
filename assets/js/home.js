(function() {
  const cardGrid = document.getElementById('home-cards');
  const cards = Array.from(cardGrid.querySelectorAll('.post-card'));
  const articlesSection = document.getElementById('articles-section');
  const featuredSection = document.getElementById('featured-tools-section');
  const searchResultsSection = document.getElementById('search-results-section');
  const searchToolsResults = document.getElementById('search-tools-results');
  const searchArticlesResults = document.getElementById('search-articles-results');
  const searchNoResults = document.getElementById('search-no-results');
  const searchResultsTitle = document.getElementById('search-results-title');
  const viewAllWrap = document.querySelector('.view-all-wrap');
  let activeSort = 'latest';
  let allTools = [];

  // Redirect ?tag= and ?category= to blog.html
  const params = new URLSearchParams(window.location.search);
  if (params.get('tag') || params.get('category')) {
    window.location.href = '/ai-pulse/blog.html' + window.location.search;
    return;
  }

  // Load featured tools
  fetch('/ai-pulse/tools/index.json')
    .then(r => r.json())
    .then(data => {
      allTools = data;
      renderFeaturedTools(data.filter(t => t.featured));
    })
    .catch(() => {
      if (featuredSection) featuredSection.style.display = 'none';
    });

  function renderFeaturedTools(tools) {
    const grid = document.getElementById('featured-tools-grid');
    if (!grid) return;
    grid.innerHTML = tools.map(tool => {
      const domain = (() => { try { return new URL(tool.url).hostname; } catch(e) { return ''; } })();
      const logoUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
      const fallback = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36'%3E%3Crect width='36' height='36' fill='%23e0e0e0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='16' fill='%23999'%3E${tool.name.charAt(0)}%3C/text%3E%3C/svg%3E`;
      return `<a href="${tool.url}" target="_blank" rel="noopener noreferrer" class="ft-card">
        <img src="${logoUrl}" alt="${tool.name}" class="ft-logo" onerror="this.src='${fallback}'" />
        <span class="ft-name">${tool.name}</span>
      </a>`;
    }).join('');
  }

  // Search
  const searchInput = document.getElementById('home-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (q.length === 0) {
        showDefault();
      } else {
        showSearchResults(q);
      }
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        searchInput.value = '';
        showDefault();
      }
    });
  }

  function showDefault() {
    featuredSection.style.display = '';
    articlesSection.style.display = '';
    cardGrid.style.display = '';
    if (viewAllWrap) viewAllWrap.style.display = '';
    searchResultsSection.style.display = 'none';
  }

  function showSearchResults(q) {
    featuredSection.style.display = 'none';
    articlesSection.style.display = 'none';
    cardGrid.style.display = 'none';
    if (viewAllWrap) viewAllWrap.style.display = 'none';
    searchResultsSection.style.display = '';

    // Filter articles
    const matchedArticles = cards.filter(card => {
      const title = card.querySelector('.post-title')?.textContent.toLowerCase() || '';
      const excerpt = card.querySelector('.post-excerpt')?.textContent.toLowerCase() || '';
      const tags = (card.dataset.tags || '').toLowerCase();
      return title.includes(q) || excerpt.includes(q) || tags.includes(q);
    });

    // Filter tools
    const matchedTools = allTools.filter(tool => {
      return tool.name.toLowerCase().includes(q) ||
        tool.description.toLowerCase().includes(q) ||
        (tool.tags || []).some(t => t.toLowerCase().includes(q));
    });

    const total = matchedArticles.length + matchedTools.length;
    searchResultsTitle.textContent = `Results for "${q}" (${total})`;

    // Render tool results
    if (matchedTools.length > 0) {
      searchToolsResults.innerHTML = `<p class="search-tools-label">Tools (${matchedTools.length})</p>
        <div class="search-tools-row">${matchedTools.slice(0, 8).map(tool => {
          const domain = (() => { try { return new URL(tool.url).hostname; } catch(e) { return ''; } })();
          const logoUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
          const fallback = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36'%3E%3Crect width='36' height='36' fill='%23e0e0e0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='16' fill='%23999'%3E${tool.name.charAt(0)}%3C/text%3E%3C/svg%3E`;
          return `<a href="${tool.url}" target="_blank" rel="noopener noreferrer" class="ft-card" style="width:80px;">
            <img src="${logoUrl}" alt="${tool.name}" class="ft-logo" onerror="this.src='${fallback}'" />
            <span class="ft-name">${tool.name}</span>
          </a>`;
        }).join('')}</div>`;
      searchToolsResults.style.display = '';
    } else {
      searchToolsResults.innerHTML = '';
      searchToolsResults.style.display = 'none';
    }

    // Render article results
    searchArticlesResults.innerHTML = '';
    if (matchedArticles.length > 0) {
      matchedArticles.forEach(card => {
        const clone = card.cloneNode(true);
        searchArticlesResults.appendChild(clone);
      });
      searchArticlesResults.style.display = '';
    } else {
      searchArticlesResults.style.display = 'none';
    }

    searchNoResults.style.display = total === 0 ? '' : 'none';
  }

  // Sort toggle
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeSort = btn.dataset.sort;
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      sortCards();
    });
  });

  function sortCards() {
    const sorted = [...cards].sort((a, b) => {
      if (activeSort === 'popular') {
        return parseInt(b.dataset.views || 0) - parseInt(a.dataset.views || 0);
      }
      return (b.dataset.date || '').localeCompare(a.dataset.date || '');
    });
    sorted.forEach(card => cardGrid.appendChild(card));
  }
})();
