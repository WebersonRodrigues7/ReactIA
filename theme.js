(function () {
  const THEME_KEY = 'tunix-theme';
  const savedTheme = localStorage.getItem(THEME_KEY);
  const theme = savedTheme === 'dark' ? 'dark' : 'light';

  document.documentElement.dataset.theme = theme;

  if (document.body) {
    document.body.dataset.theme = theme;
  } else {
    window.addEventListener('DOMContentLoaded', () => {
      document.body.dataset.theme = theme;
    });
  }
})();
