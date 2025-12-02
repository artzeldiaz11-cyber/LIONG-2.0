class InventorySidebar extends HTMLElement {
  connectedCallback() {
    const currentFile = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();

    const menu = [
      { href: '/inventory-dashboard/', label: 'Inventory Dashboard', icon: 'layers' },
      { href: '/inventory-dashboard/stock-in/', label: 'Stock In', icon: 'arrow-down-circle' },
      { href: '/inventory-dashboard/stock-out/', label: 'Stock Out', icon: 'arrow-up-circle' },
      { href: '/inventory-dashboard/balance/', label: 'Balance', icon: 'bar-chart-2' },
      { href: '/inventory-dashboard/approved_requisitions/', label: 'Manage Request', icon: 'fa-solid fa-gear' },
      { href: '/inventory-dashboard/conversion/', label: 'Conversion Table', icon: 'shuffle' }
    ];

    const makeIconSvg = (name) => {
      try {
        if (window.feather && window.feather.icons && window.feather.icons[name]) {
          return window.feather.icons[name].toSvg({ class: 'icon' });
        }
      } catch (e) { }
      return `<i data-feather="${name}" class="icon"></i>`;
    };

    const itemsHtml = menu.map(item => {
      const itemPath = new URL(item.href, window.location.origin).pathname.toLowerCase();
      const isActive = currentFile === itemPath.split('/').pop() || currentFile === itemPath.slice(1, -1);
      return `
        <li>
          <a href="${item.href}" class="menu-item ${isActive ? 'active' : ''}">
            ${makeIconSvg(item.icon)}
            <span class="label">${item.label}</span>
          </a>
        </li>
      `;
    }).join('');

    this.innerHTML = `
      <style>
        .custom-sidebar {
          width: 250px;
          background: #f8fafc;
          padding: 1rem;
          height: 100vh;
          position: fixed;
          left: 0;
          top: 0;
          border-right: 1px solid #e5e7eb;
          z-index: 40;
          box-sizing: border-box;
        }
        .custom-sidebar .department-head { padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid #e5e7eb; }
        .custom-sidebar .department-head h3 { font-weight: 600; margin: 0; font-size: 1rem; color: #111827; }
        .custom-sidebar .department-head p { font-size: 0.875rem; color: #6b7280; margin: 0.25rem 0 0 0; }
        .custom-sidebar .nav-links { list-style: none; padding: 0; margin: 1rem 0 0 0; }
        .custom-sidebar .menu-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0.8rem; color: #4b5563; text-decoration: none; border-radius: 0.375rem; transition: background 0.15s, color 0.15s; border-left: 3px solid transparent; }
        .custom-sidebar .menu-item:hover { background-color: #eef2ff; color: #1e40af; }
        .custom-sidebar .menu-item.active { background-color: #e0e7ff; color: #1e40af; font-weight: 600; border-left-color: #c7d2fe; }
        .custom-sidebar .icon { width: 18px; height: 18px; stroke: currentColor; }
        @media (max-width: 768px) {
          .custom-sidebar { transform: translateX(-100%); transition: transform .25s ease; }
          .custom-sidebar.open { transform: translateX(0); }
        }
      </style>
      <aside class="custom-sidebar">
        <div class="department-head">
          <h3>Inventory</h3>
          <p>Management System</p>
        </div>
        <ul class="nav-links">
          ${itemsHtml}
        </ul>
      </aside>
    `;

    setTimeout(() => feather.replace(), 20);
    setTimeout(() => feather.replace(), 200);
  }
}

customElements.define('inventory-sidebar', InventorySidebar);