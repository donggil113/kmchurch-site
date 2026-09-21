const menu = document.querySelector('#site-menu');
const openButton = document.querySelector('.menu-toggle');
const closeButton = document.querySelector('.menu-close');
let previousFocus = null;

function openMenu() {
  previousFocus = document.activeElement;
  menu.hidden = false;
  document.body.classList.add('menu-open');
  openButton.setAttribute('aria-expanded', 'true');
  closeButton.focus();
}

function closeMenu() {
  menu.hidden = true;
  document.body.classList.remove('menu-open');
  openButton.setAttribute('aria-expanded', 'false');
  previousFocus?.focus();
}

openButton?.addEventListener('click', openMenu);
document.querySelector('.footer-sitemap')?.addEventListener('click', openMenu);
closeButton?.addEventListener('click', closeMenu);
menu?.addEventListener('click', event => { if (event.target === menu) closeMenu(); });
document.addEventListener('keydown', event => {
  if (!menu) return;
  if (event.key === 'Escape' && !menu.hidden) closeMenu();
  if (event.key === 'Tab' && !menu.hidden) {
    const focusable = [...menu.querySelectorAll('a, button')];
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});

const migratedCodes = new Set([1, 78, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 19, 17, 18, 51, 20, 81, 21, 38, 33, 39, 82, 29, 44, 30, 34, 35, 31, 46, 79, 87, 48, 84, 43, 36, 41, 37]);
const groupDefault = { 1: 1, 2: 13, 3: 20, 5: 33, 6: 46 };
const fromSubpage = location.pathname.includes('/pages/');
document.querySelectorAll('a[href]').forEach(link => {
  try {
    const url = new URL(link.href);
    if (url.hostname !== 'kmchurch.kr' || url.pathname !== '/main/sub.html') return;
    if (url.searchParams.has('Mode') || url.searchParams.has('boardID')) return;
    const code = Number(url.searchParams.get('pageCode')) || groupDefault[Number(url.searchParams.get('mstrCode'))];
    if (migratedCodes.has(code)) link.href = `${fromSubpage ? '' : 'pages/'}${code}.html`;
  } catch { /* Keep an unusual external URL unchanged. */ }
});

document.querySelectorAll('.archive-canvas').forEach(wrapper => {
  const canvas = wrapper.querySelector('.awcBaseLayer');
  if (!canvas) return;
  const originalWidth = parseFloat(canvas.style.width) || 800;
  const originalHeight = parseFloat(canvas.style.height) || canvas.scrollHeight;
  const fit = () => {
    const scale = Math.min(1, wrapper.clientWidth / originalWidth);
    canvas.style.transform = `scale(${scale})`;
    wrapper.style.height = `${Math.ceil(originalHeight * scale)}px`;
  };
  fit();
  new ResizeObserver(fit).observe(wrapper);
});
