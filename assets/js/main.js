// Load and render post list from posts/index.json
async function loadPosts() {
  const listEl = document.getElementById('post-list');
  if (!listEl) return;

  try {
    const res = await fetch('posts/index.json');
    if (!res.ok) throw new Error('No posts yet');
    const posts = await res.json();

    if (!posts.length) {
      listEl.innerHTML = '<div class="empty">No articles yet. Check back soon.</div>';
      return;
    }

    // Build tag filter buttons
    const tags = [...new Set(posts.flatMap(p => p.tags || []))].sort();
    const filtersEl = document.querySelector('.filters');
    tags.forEach(tag => {
      const btn = document.createElement('button');
      btn.className = 'filter-btn';
      btn.dataset.tag = tag;
      btn.textContent = '#' + tag;
      filtersEl.appendChild(btn);
    });

    // Filter logic
    let activeTag = 'all';
    filtersEl.addEventListener('click', e => {
      const btn = e.target.closest('.filter-btn');
      if (!btn) return;
      activeTag = btn.dataset.tag;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderPosts(posts, activeTag);
    });

    renderPosts(posts, activeTag);
  } catch (e) {
    listEl.innerHTML = '<div class="empty">No articles yet. Check back soon.</div>';
  }
}

function renderPosts(posts, tag) {
  const listEl = document.getElementById('post-list');
  const filtered = tag === 'all' ? posts : posts.filter(p => (p.tags || []).includes(tag));

  if (!filtered.length) {
    listEl.innerHTML = '<div class="empty">No articles for this tag.</div>';
    return;
  }

  listEl.innerHTML = filtered.map(post => `
    <a class="post-card" href="posts/${post.slug}.html">
      <div class="post-meta">
        <span class="post-date">${formatDate(post.date)}</span>
        ${post.level ? `<span class="post-level">${post.level}</span>` : ''}
      </div>
      <div class="post-title">${escHtml(post.title)}</div>
      <div class="post-excerpt">${escHtml(post.excerpt || '')}</div>
      <div class="post-tags">
        ${(post.tags || []).map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}
      </div>
    </a>
  `).join('');
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
