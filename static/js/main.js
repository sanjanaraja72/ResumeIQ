const root = document.documentElement;
const saved = localStorage.getItem('theme');
if (saved) root.setAttribute('data-theme', saved);

const btn = document.getElementById('themeBtn');
const icon = () => { if (btn) btn.textContent = root.getAttribute('data-theme') === 'dark' ? '🌙' : '☀️'; };
icon();
if (btn) btn.addEventListener('click', () => {
  const t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  icon();
});

// drag & drop upload
document.querySelectorAll('.drop').forEach(drop => {
  const input = drop.querySelector('input[type=file]');
  const title = drop.querySelector('.drop-title');
  const show = () => {
    if (input.files.length) { title.textContent = '✅ ' + input.files[0].name; drop.classList.add('has-file'); }
  };
  input.addEventListener('change', show);
  ['dragenter', 'dragover'].forEach(e => drop.addEventListener(e, ev => { ev.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(e => drop.addEventListener(e, ev => { ev.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', ev => { input.files = ev.dataTransfer.files; show(); });
});

// loading overlay
document.querySelectorAll('form[data-loader]').forEach(f => f.addEventListener('submit', () => {
  const l = document.createElement('div');
  l.className = 'loader';
  l.innerHTML = '<div class="spin"></div><p>Analyzing with AI...</p>';
  document.body.appendChild(l);
}));

// result page animations
window.addEventListener('load', () => {
  document.querySelectorAll('.ring-fg').forEach(c => {
    c.style.strokeDashoffset = 327 * (1 - (+c.dataset.score) / 100);
  });
  document.querySelectorAll('[data-count]').forEach(el => {
    const end = +el.dataset.count; let n = 0;
    const step = Math.max(1, Math.round(end / 40));
    const t = setInterval(() => { n = Math.min(end, n + step); el.textContent = n; if (n >= end) clearInterval(t); }, 25);
  });
  document.querySelectorAll('.bar-fill').forEach(b => { b.style.width = b.dataset.w + '%'; });

  const rc = document.getElementById('roleChart');
  if (rc && window.Chart) {
    new Chart(rc, {
      type: 'bar',
      data: {
        labels: JSON.parse(rc.dataset.labels),
        datasets: [{ data: JSON.parse(rc.dataset.values), borderRadius: 8, backgroundColor: 'rgba(124,92,255,.75)' }]
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: {
          x: { max: 100, ticks: { color: '#9aa0c3' }, grid: { color: 'rgba(150,150,200,.15)' } },
          y: { ticks: { color: '#9aa0c3' }, grid: { display: false } }
        }
      }
    });
  }
});