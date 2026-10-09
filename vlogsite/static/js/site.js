document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const category = (params.get('category') || '').trim();
  const searchText = (params.get('q') || '').trim().toLowerCase();

  const filterGrid = document.querySelector('.video-grid');
  if (filterGrid) {
    const cards = Array.from(filterGrid.querySelectorAll('.video-card'));
    let visibleCount = 0;

    cards.forEach((card) => {
      const cardCategory = (card.querySelector('.category')?.textContent || '').trim();
      const cardText = card.textContent.toLowerCase();
      const categoryMatches = !category || cardCategory === category;
      const searchMatches = !searchText || cardText.includes(searchText);

      const shouldShow = categoryMatches && searchMatches;
      card.style.display = shouldShow ? '' : 'none';
      if (shouldShow) visibleCount += 1;
    });

    const emptyState = document.querySelector('.empty-state');
    if (emptyState) {
      emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  const chips = document.querySelectorAll('.chip');
  chips.forEach((chip) => {
    const href = chip.getAttribute('href') || '';
    const url = new URL(href, window.location.origin);
    const chipCategory = url.searchParams.get('category') || '';
    if (chipCategory === category || (!chipCategory && !category)) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });

  document.querySelectorAll('[data-static-form]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const formType = form.dataset.staticForm || 'Form';
      const inputSummary = Array.from(new FormData(form).entries())
        .filter(([, value]) => value && String(value).trim())
        .map(([key, value]) => `${key}: ${value}`)
        .join(' | ');

      const message = [
        `${formType} submissions are disabled in this static GitHub Pages version because the site does not run the Flask backend or SQLite database.`,
        'Your typed information was not sent anywhere.',
        inputSummary ? `Draft values entered: ${inputSummary}` : 'No values were entered.',
        'To submit this form, use the original Flask app or deploy with a backend service.'
      ].join(' ');

      let note = form.parentElement.querySelector('.static-form-message');
      if (!note) {
        note = document.createElement('p');
        note.className = 'static-form-message';
        form.parentElement.appendChild(note);
      }

      note.textContent = message;
      note.style.marginTop = '12px';
      note.style.color = '#9C4B2A';
      note.style.fontWeight = '600';
      note.style.lineHeight = '1.5';
    });
  });
});
