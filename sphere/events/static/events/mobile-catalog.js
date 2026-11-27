const catalogIndex = document.getElementById('catalog');
const catalogBack = document.querySelector('.mobile-catalog-back');
if (catalogIndex && catalogBack) {
  const updateBackLink = () => {
    catalogBack.hidden = catalogIndex.getBoundingClientRect().bottom > 0;
  };
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(updateBackLink);
    observer.observe(catalogIndex);
  } else {
    window.addEventListener('scroll', updateBackLink, { passive: true });
  }
  window.addEventListener('resize', updateBackLink, { passive: true });
  updateBackLink();
}

// One HTML component: disclosures start closed on narrow screens, open on desktop.
const catalogWide = window.matchMedia('(min-width: 1024px)');
const updateCatalogDisclosures = () => {
  document.querySelectorAll('.mobile-concept, .mobile-about > details').forEach((details) => {
    details.open = catalogWide.matches;
  });
};
catalogWide.addEventListener('change', updateCatalogDisclosures);
updateCatalogDisclosures();
