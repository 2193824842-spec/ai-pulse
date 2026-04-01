// Load and render post list from posts/index.json
let allPosts = [];
let activeTag = 'all';
let searchQuery = '';

async function loadPosts() {
  const listEl = document.getElementById('post-list');
  if (!listEl) return;

  try {
    const res = await fetch('posts/index.json');
    if (!res.ok) throw new Error('No posts yet');
    allPosts = await res.json();

    if (!allPosts.length) {
      listEl.innerHTML = '<div class="empty">No articles yet. Check back soon.</div>';
      return;
    }

    // Build tag filter buttons
    const tags = [...new Set(allPosts.flatMap(p => p.tags || []))].sort();
    const filtersEl = document.querySelector('.filters');
    tags.forEach(tag => {
      const btn = document.createElement('button');
      btn.className = 'filter-btn';
      btn.dataset.tag = tag;
      btn.textContent = '#' + tag;
      filtersEl.appendChild(btn);
    });

    // Filter click
    filtersEl.addEventListener('click', e => {
      const btn = e.target.closest('.filter-btn');
      if (!btn) return;
      activeTag = btn.dataset.tag;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderPosts();
    });

    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', e => {
        searchQuery = e.target.value.trim().toLowerCase();
        renderPosts();
      });
    }

    renderPosts();
  } catch (e) {
    listEl.innerHTML = '<div class="empty">No articles yet. Check back soon.</div>';
  }
}

function renderPosts() {
  const listEl = document.getElementById('post-list');
  let filtered = allPosts;

  // Tag filter
  if (activeTag !== 'all') {
    filtered = filtered.filter(p => (p.tags || []).includes(activeTag));
  }

  // Search filter
  if (searchQuery) {
    filtered = filtered.filter(p => {
      const title = (p.title || '').toLowerCase();
      const excerpt = (p.excerpt || '').toLowerCase();
      const tags = (p.tags || []).join(' ').toLowerCase();
      return title.includes(searchQuery) || excerpt.includes(searchQuery) || tags.includes(searchQuery);
    });
  }

  if (!filtered.length) {
    const msg = searchQuery ? `No results for "${searchQuery}"` : 'No articles for this tag.';
    listEl.innerHTML = `<div class="empty">${escHtml(msg)}</div>`;
    return;
  }

  listEl.innerHTML = filtered.map(post => `
    <a class="post-card" href="posts/${post.slug}.html">
      <div class="post-meta">
        <span class="post-date">${formatDate(post.date)}</span>
        ${post.level ? `<span class="post-level">${post.level}</span>` : ''}
      </div>
      <div class="post-title">${highlightMatch(escHtml(post.title))}</div>
      <div class="post-excerpt">${highlightMatch(escHtml(post.excerpt || ''))}</div>
      <div class="post-tags">
        ${(post.tags || []).map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}
      </div>
    </a>
  `).join('');
}

function highlightMatch(text) {
  if (!searchQuery) return text;
  const escaped = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>');
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

loadPosts();
