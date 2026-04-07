(function() {
  const postList = document.getElementById('post-list');
  const cards = Array.from(postList.querySelectorAll('.post-card'));
  let activeTag = 'all';
  let activeCategory = 'all';
  let activeSort = 'latest';
  let searchQuery = '';

  // URL params
  const params = new URLSearchParams(window.location.search);
  const urlTag = params.get('tag');
  const urlCat = params.get('category');
  const urlQ = params.get('q');

  if (urlTag) {
    activeTag = urlTag;
    const btn = document.querySelector(`.tag-btn[data-tag="${urlTag}"]`);
    if (btn) {
      document.querySelector('[data-tag="all"]').classList.remove('active');
      btn.classList.add('active');
    }
  }
  if (urlCat) {
    activeCategory = urlCat;
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.cat-btn[data-cat="${urlCat}"]`);
    if (btn) btn.classList.add('active');
  }
  if (urlQ) {
    searchQuery = urlQ.toLowerCase();
    const input = document.getElementById('search-input');
    if (input) input.value = urlQ;
  }

  // Category buttons
  document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeCategory = btn.dataset.cat;
      document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterAndSort();
    });
  });

  // Tag buttons
  document.querySelectorAll('.tag-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.tag;
      if (tag === 'all') { activeTag = 'all'; }
      else { activeTag = activeTag === tag ? 'all' : tag; }
      document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
      if (activeTag === 'all') {
        document.querySelector('[data-tag="all"]').classList.add('active');
      } else {
        btn.classList.add('active');
      }
      filterAndSort();
    });
  });

  // Sort buttons
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeSort = btn.dataset.sort;
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterAndSort();
    });
  });

  // Search
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      searchQuery = searchInput.value.trim().toLowerCase();
      filterAndSort();
    });
  }

  function filterAndSort() {
    let visible = [];
    cards.forEach(card => {
      const cat = card.dataset.cat || '';
      const tags = (card.dataset.tags || '').split(',');
      const title = card.querySelector('.post-title').textContent.toLowerCase();
      const excerpt = card.querySelector('.post-excerpt').textContent.toLowerCase();

      let show = true;
      if (activeCategory !== 'all' && cat !== activeCategory) show = false;
      if (activeTag !== 'all' && !tags.includes(activeTag)) show = false;
      if (searchQuery && !title.includes(searchQuery) && !excerpt.includes(searchQuery) && !tags.some(t => t.includes(searchQuery))) show = false;

      card.style.display = show ? '' : 'none';
      if (show) visible.push(card);
    });

    // Sort visible cards
    visible.sort((a, b) => {
      if (activeSort === 'popular') {
        return parseInt(b.dataset.views || 0) - parseInt(a.dataset.views || 0);
      }
      return (b.dataset.date || '').localeCompare(a.dataset.date || '');
    });

    // Reorder DOM
    visible.forEach(card => postList.appendChild(card));
    // Move hidden cards to end
    cards.filter(c => c.style.display === 'none').forEach(c => postList.appendChild(c));
  }

  // Initial filter
  filterAndSort();
})();
