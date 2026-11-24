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
