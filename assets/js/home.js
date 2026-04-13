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
  let allArticles = [];

  // Redirect ?tag= and ?category= to blog.html
  const params = new URLSearchParams(window.location.search);
  if (params.get('tag') || params.get('category')) {
    window.location.href = '/ai-pulse/blog.html' + window.location.search;
    return;
  }

  // Load tools and articles in parallel
  Promise.all([
    fetch('/ai-pulse/tools/index.json').then(r => r.json()).catch(() => []),
    fetch('/ai-pulse/posts/index.json').then(r => r.json()).catch(() => [])
  ]).then(([tools, articles]) => {
    allTools = tools;
    allArticles = articles;
    renderFeaturedTools(tools.filter(t => t.featured));
    const statTools = document.getElementById('stat-tools');
    if (statTools) statTools.textContent = tools.length;
    const statArticles = document.getElementById('stat-articles');
    if (statArticles) statArticles.textContent = articles.length;
  });

  function toolSlug(name) {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  function renderFeaturedTools(tools) {
    const grid = document.getElementById('featured-tools-grid');
    if (!grid) return;
    grid.innerHTML = tools.map(tool => {
      const domain = (() => { try { return tool.favicon_domain || new URL(tool.url).hostname; } catch(e) { return ''; } })();
      const logoUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
      const fallback = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36'%3E%3Crect width='36' height='36' fill='%23e0e0e0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='16' fill='%23999'%3E${tool.name.charAt(0)}%3C/text%3E%3C/svg%3E`;
      const detailUrl = `/ai-pulse/tools/${toolSlug(tool.name)}.html`;
      return `<a href="${detailUrl}" class="ft-card">
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

    // Filter articles from full index
    const matchedArticles = allArticles.filter(a => {
      return (a.title || '').toLowerCase().includes(q) ||
        (a.excerpt || '').toLowerCase().includes(q) ||
        (a.tags || []).some(t => t.toLowerCase().includes(q)) ||
        (a.category || '').toLowerCase().includes(q);
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
          const domain = (() => { try { return tool.favicon_domain || new URL(tool.url).hostname; } catch(e) { return ''; } })();
          const logoUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
          const fallback = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36'%3E%3Crect width='36' height='36' fill='%23e0e0e0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='16' fill='%23999'%3E${tool.name.charAt(0)}%3C/text%3E%3C/svg%3E`;
          return `<a href="/ai-pulse/tools/${toolSlug(tool.name)}.html" class="ft-card" style="width:80px;">
            <img src="${logoUrl}" alt="${tool.name}" class="ft-logo" onerror="this.src='${fallback}'" />
            <span class="ft-name">${tool.name}</span>
          </a>`;
        }).join('')}</div>`;
      searchToolsResults.style.display = '';
    } else {
      searchToolsResults.innerHTML = '';
      searchToolsResults.style.display = 'none';
    }

    // Render article results from full index
    searchArticlesResults.innerHTML = '';
    if (matchedArticles.length > 0) {
      const label = document.createElement('p');
      label.className = 'search-tools-label';
      label.textContent = `Articles (${matchedArticles.length})`;
      searchArticlesResults.appendChild(label);
      const grid = document.createElement('div');
      grid.className = 'card-grid';
      matchedArticles.forEach(a => {
        const tags = (a.tags || []).slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('');
        const date = a.date ? new Date(a.date).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '';
        grid.innerHTML += `<a href="/ai-pulse/posts/${a.slug}.html" class="post-card">
          <div class="card-cover">
            <img src="/ai-pulse/assets/images/${a.slug}.jpg" alt="${a.title}" loading="lazy" onerror="this.style.display='none'" />
            <span class="card-cat-badge">${a.category || ''}</span>
            <span class="card-date-badge">${date}</span>
          </div>
          <div class="post-card-body">
            <h2 class="post-title">${a.title}</h2>
            <p class="post-excerpt">${a.excerpt || ''}</p>
            <div class="post-card-footer">
              <div class="post-tags">${tags}</div>
            </div>
          </div>
        </a>`;
      });
      searchArticlesResults.appendChild(grid);
      searchArticlesResults.style.display = 'block';
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
