class CustomSidebar extends HTMLElement {
  connectedCallback() {
    // Render into light DOM so feather.replace() can operate and page styles apply
    const currentFile = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();

    const menu = [
      { href: 'overview.html', label: 'Overview', icon: 'home' },
      { href: 'employees.html', label: 'Employee Management', icon: 'users' },
      { href: 'requests.html', label: 'Requests', icon: 'file-text' }
    ];

    const makeIconSvg = (name) => {
      try {
        if (window.feather && window.feather.icons && window.feather.icons[name]) {
          return window.feather.icons[name].toSvg({ class: 'icon' });
        }
      } catch (e) { /* fallback below */ }
      return `<i data-feather="${name}" class="icon"></i>`;
    };

    const itemsHtml = menu.map(item => {
      const itemFile = item.href.split('/').pop().toLowerCase();
      const isActive = itemFile === currentFile;
      return `
        <li>
          <a href="${item.href}" class="menu-item ${isActive ? 'active' : ''}" aria-current="${isActive ? 'page' : 'false'}">
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
        .custom-sidebar .department-head { padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid #e5e7eb;}
        .custom-sidebar .department-head h3 { font-weight: 600; margin: 0; font-size: 1rem; color:#111827; }
        .custom-sidebar .department-head p { font-size: 0.875rem; color: #6b7280; margin: 0.25rem 0 0 0; }
        .custom-sidebar .nav-links { list-style: none; padding: 0; margin: 1rem 0 0 0; display:block; }
        .custom-sidebar .nav-links li { margin-bottom: 0.25rem; }
        .custom-sidebar .menu-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.6rem 0.8rem;
          color: #4b5563;
          text-decoration: none;
          border-radius: 0.375rem;
          transition: background 0.15s, color 0.15s;
          border-left: 3px solid transparent;
        }
        .custom-sidebar .menu-item:hover { background-color: #eef2ff; color: #1e40af; }
        .custom-sidebar .menu-item.active {
          background-color: #e0e7ff;
          color: #1e40af;
          font-weight: 600;
          border-left-color: #c7d2fe;
        }
        .custom-sidebar .icon { width: 18px; height: 18px; flex-shrink:0; stroke: currentColor; }
        .custom-sidebar .label { font-size: 0.95rem; color: inherit; }
        @media (max-width: 768px) {
          .custom-sidebar { transform: translateX(-100%); position: fixed; transition: transform .25s ease; }
          .custom-sidebar.open { transform: translateX(0); }
        }
      </style>

      <aside class="custom-sidebar" role="navigation" aria-label="Main sidebar">
        <div class="department-head">
          <h3>Department Head</h3>
          <p>Inventory Management</p>
        </div>
        <ul class="nav-links">
          ${itemsHtml}
        </ul>
      </aside>
    `;

    // Replace feather icons now (if feather is loaded). If not loaded yet, try shortly after.
    const tryReplace = () => {
      if (window.feather && typeof window.feather.replace === 'function') {
        window.feather.replace();
      }
    };
    tryReplace();
    // safe retry if feather is loaded asynchronously
    setTimeout(tryReplace, 50);
    setTimeout(tryReplace, 250);
  }
}

customElements.define('custom-sidebar', CustomSidebar);