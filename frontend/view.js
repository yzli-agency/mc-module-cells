/**
 * yzli/cells — Frontend view
 * Constellation des cellules et rôles.
 */
(function () {
  const view = document.createElement('div');
  view.id = 'view-cells-v2';
  view.className = 'view module-view';
  view.innerHTML = `
    <div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
        <h1 style="font-size:1.4rem">Constellation</h1>
        <button onclick="cellsV2Load()" style="background:var(--surface);border:1px solid var(--border);padding:0.4rem 0.8rem;border-radius:6px;cursor:pointer;font-size:0.8rem;color:var(--text)">↻ Refresh</button>
      </div>
      <div id="cells-v2-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem"></div>
    </div>`;
  document.getElementById('main').appendChild(view);

  async function cellsV2Load() {
    try {
      const cells = await mcApi('/api/cells-v2');
      const el = document.getElementById('cells-v2-grid');
      el.innerHTML = cells.map(cell => `
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.25rem">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem">
            <span style="font-size:1.5rem">${cell.emoji || '🔷'}</span>
            <div>
              <div style="font-weight:600">${cell.name}</div>
              <div style="font-size:0.72rem;color:var(--muted)">${cell.mode} · ${cell.status}</div>
            </div>
          </div>
          ${cell.description ? `<p style="font-size:0.8rem;color:var(--muted);margin-bottom:0.75rem">${cell.description}</p>` : ''}
          <div>
            ${(cell.roles || []).map(r => `
              <div style="display:flex;align-items:center;justify-content:space-between;padding:0.4rem 0;border-top:1px solid var(--border)">
                <span style="font-size:0.8rem">${r.name}</span>
                <div style="display:flex;gap:0.25rem">
                  ${r.is_lead ? '<span style="font-size:0.65rem;background:var(--accent-dim);color:var(--accent);padding:0.1rem 0.3rem;border-radius:3px">lead</span>' : ''}
                  <span style="font-size:0.65rem;color:var(--muted);background:var(--bg);padding:0.1rem 0.3rem;border-radius:3px">${r.level}</span>
                </div>
              </div>`).join('') || '<p style="font-size:0.75rem;color:var(--muted)">Aucun rôle</p>'}
          </div>
        </div>`).join('');
    } catch (e) { console.error('[cells-v2]', e); }
  }

  window.cellsV2Load = cellsV2Load;

  document.addEventListener('click', e => {
    if (e.target.closest('[data-view="cells-v2"]')) cellsV2Load();
  });
})();
