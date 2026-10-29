// FinAgent · Enhancements de interfaz y branding institucional
document.addEventListener('DOMContentLoaded', () => {
  console.log("💎 FinAgent Theme Loaded · ISFT N° 197");

  const replaceLogo = () => {
    // 1. Reemplazar logo en la pantalla de login o header
    const links = document.querySelectorAll('a[href="/"], div.flex.items-center, header');
    links.forEach(el => {
      // Buscar elementos con texto Chainlit
      if (el.textContent && el.textContent.includes('Chainlit') && !el.dataset.logoReplaced) {
        el.dataset.logoReplaced = "true";
        el.innerHTML = `
          <div style="display:flex; align-items:center; gap:10px; cursor:pointer;">
            <div style="background:#0D1524; border:1px solid #D4AF37; width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 12px rgba(212,175,55,0.25);">
              <span style="font-family:'Playfair Display', serif; color:#D4AF37; font-weight:700; font-size:1.15rem; line-height:1;">§</span>
            </div>
            <div style="display:flex; flex-direction:column;">
              <span style="font-family:'Plus Jakarta Sans', sans-serif; font-weight:700; font-size:1.05rem; letter-spacing:0.02em; color:#FFFFFF;">Fin<span style="color:#D4AF37;">Agent</span></span>
              <span style="font-family:'JetBrains Mono', monospace; font-size:0.58rem; color:#10B981; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;">Asesor Financiero IA</span>
            </div>
          </div>
        `;
      }
    });

    // 2. Inyectar insignia institucional en el header superior
    const header = document.querySelector('header');
    if (header && !document.getElementById('finagent-badge')) {
      const badge = document.createElement('div');
      badge.id = 'finagent-badge';
      badge.style.display = 'inline-flex';
      badge.style.alignItems = 'center';
      badge.style.gap = '8px';
      badge.style.fontSize = '0.74rem';
      badge.style.fontFamily = "'JetBrains Mono', monospace";
      badge.style.letterSpacing = '0.06em';
      badge.style.color = '#D4AF37';
      badge.style.background = 'rgba(212, 175, 55, 0.08)';
      badge.style.border = '1px solid rgba(212, 175, 55, 0.25)';
      badge.style.padding = '4px 12px';
      badge.style.borderRadius = '9999px';
      badge.style.marginLeft = '16px';
      badge.innerHTML = '<span style="color:#10B981; font-size:0.65rem;">●</span> ISFT N° 197 · Proyecto Integrador';
      
      const leftContainer = header.querySelector('div');
      if (leftContainer) {
        leftContainer.appendChild(badge);

        if (!document.getElementById('finagent-dash-btn')) {
          const dashBtn = document.createElement('a');
          dashBtn.id = 'finagent-dash-btn';
          dashBtn.href = '/public/dashboard.html';
          dashBtn.target = '_blank';
          dashBtn.style.display = 'inline-flex';
          dashBtn.style.alignItems = 'center';
          dashBtn.style.gap = '6px';
          dashBtn.style.fontSize = '0.75rem';
          dashBtn.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
          dashBtn.style.fontWeight = '600';
          dashBtn.style.color = '#090E17';
          dashBtn.style.background = 'linear-gradient(135deg, #D4AF37, #AA820A)';
          dashBtn.style.padding = '5px 13px';
          dashBtn.style.borderRadius = '6px';
          dashBtn.style.marginLeft = '12px';
          dashBtn.style.textDecoration = 'none';
          dashBtn.style.boxShadow = '0 2px 8px rgba(212, 175, 55, 0.35)';
          dashBtn.innerHTML = 'Dashboard';
          leftContainer.appendChild(dashBtn);
        }
      }
    }
  };

  // Ejecución inicial y reactiva
  replaceLogo();
  const observer = new MutationObserver(replaceLogo);
  observer.observe(document.body, { childList: true, subtree: true });
});
