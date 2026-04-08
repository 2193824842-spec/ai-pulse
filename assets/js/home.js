(function() {
  const cardGrid = document.getElementById('home-cards');
  const cards = Array.from(cardGrid.querySelectorAll('.post-card'));
  let activeSort = 'latest';

  // Redirect ?tag= and ?category= to blog.html
  const params = new URLSearchParams(window.location.search);
  if (params.get('tag') || params.get('category')) {
    window.location.href = '/ai-pulse/blog.html' + window.location.search;
    return;
  }

  // Search redirect to blog.html
  const searchInput = document.getElementById('home-search');
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = searchInput.value.trim();
        if (q) {
          window.location.href = '/ai-pulse/blog.html?q=' + encodeURIComponent(q);
        }
      }
    });
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
