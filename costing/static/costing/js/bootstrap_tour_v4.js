(function(){
  const steps = [
    { selector: 'body', title: 'Welcome to SATIN Creative Studio', text: 'This updated tour matches the safer accounting, POS, inventory, payments, analytics, and daily operations workflow.' },
    { selector: '.sidebar, .mobile-topbar', title: 'Navigation', text: 'Use the sidebar or mobile menu to move between Dashboard, Quote Calculator, POS, Orders, Materials, Analytics, Cashflow, and Admin tools.' },
    { selector: 'a[href$="/quote/"]', title: 'Quote Calculator', text: 'Use the calculator for custom jobs. V4.3 supports safer backend calculation, custom sizing, minimum pricing, and margin checks.' },
    { selector: '#stickerSize, #customWidth', title: 'Preset or Custom Size', text: 'Choose a preset or enter custom width and height. Custom dimensions are used to calculate fit per sheet and sheets needed.' },
    { selector: '#useCricutSafeArea', title: 'Cricut / Print-only Mode', text: 'Turn Cricut safe area on for print-then-cut jobs. Turn it off for photo prints, invitations, and full-paper printing.' },
    { selector: '#materialCost, a[href$="/materials/"]', title: 'Materials and Cost Updates', text: 'Keep material pack price, pack quantity, stock, and reorder level updated. Supplier price changes flow into quotes and POS margins.' },
    { selector: 'a[href$="/pos/"]', title: 'Fast Counter POS', text: 'Use POS for ready-made offers like 4 for ₱100. V4.3 protects checkout with stock checks and transaction-safe deduction.' },
    { selector: 'a[href$="/pos/products/"]', title: 'Editable POS Products', text: 'Manage POS buttons, linked materials, selling prices, bundle quantities, and low-margin warnings when supply prices increase.' },
    { selector: 'a[href$="/queue/"]', title: 'Order Queue', text: 'Track daily production from New to Printing, Cutting, Packing, Ready, Released, Cancelled, or Refunded.' },
    { selector: 'a[href$="/cashflow/"]', title: 'Payments, Deposits, and Balances', text: 'V4.3 separates product revenue, tax, shipping, deposits, balances, and collected cash for better accounting visibility.' },
    { selector: 'a[href$="/expenses/"]', title: 'Expenses and Net Income', text: 'Record expenses so analytics can show real net income, not only gross profit from orders.' },
    { selector: 'a[href$="/analytics/"]', title: 'Analytics', text: 'Review revenue, cost, gross profit, net income, product ranking, top customers, material usage, and stock alerts.' },
    { selector: 'a[href$="/admin/"]', title: 'ERP Admin Back Office', text: 'Use Django Admin for owner-level monitoring, corrections, stock-in records, audit trail, and pricing/master data management.' },
    { selector: '[data-v4-tour-start]', title: 'Restart Anytime', text: 'Click Guided Tour or the help button anytime to repeat this walkthrough. Use it when training staff or reviewing new features.' }
  ];

  let index = 0;
  let activeSteps = [];
  let highlighted = null;

  function qs(selector){ try { return document.querySelector(selector); } catch(e){ return null; } }
  function visible(el){
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  }
  function buildSteps(){ activeSteps = steps.filter(s => s.selector === 'body' || visible(qs(s.selector))); if (!activeSteps.length) activeSteps = [steps[0]]; }
  function el(id){ return document.getElementById(id); }
  function clearHighlight(){ if (highlighted) highlighted.classList.remove('v4-tour-highlight','v4-tour-pulse'); highlighted = null; }
  function openMobileMenuIfNeeded(step){
    if (window.innerWidth >= 992) return;
    if (!step.selector || !step.selector.includes('href')) return;
    const menu = el('mobileMenu');
    if (!menu || menu.classList.contains('show')) return;
    const Offcanvas = window.bootstrap && window.bootstrap.Offcanvas;
    if (Offcanvas) Offcanvas.getOrCreateInstance(menu).show();
  }
  function placeCard(target){
    const card = el('v4TourCard');
    if (!card) return;
    if (!target || target === document.body || window.innerWidth < 992){
      card.style.left = '50%'; card.style.top = '50%'; card.style.transform = 'translate(-50%, -50%)'; return;
    }
    card.style.transform = 'none';
    const rect = target.getBoundingClientRect();
    const cardRect = card.getBoundingClientRect();
    let left = rect.right + 18;
    let top = Math.max(18, rect.top);
    if (left + cardRect.width > window.innerWidth - 18) left = rect.left - cardRect.width - 18;
    if (left < 18) left = 18;
    if (top + cardRect.height > window.innerHeight - 18) top = window.innerHeight - cardRect.height - 18;
    card.style.left = left + 'px'; card.style.top = top + 'px';
  }
  function showStep(){
    clearHighlight();
    const step = activeSteps[index];
    if (!step) return endTour();
    openMobileMenuIfNeeded(step);
    setTimeout(() => {
      const target = step.selector === 'body' ? document.body : qs(step.selector);
      if (target && target !== document.body){
        target.scrollIntoView({behavior:'smooth', block:'center', inline:'center'});
        target.classList.add('v4-tour-highlight','v4-tour-pulse');
        highlighted = target;
      }
      if (el('v4TourTitle')) el('v4TourTitle').textContent = step.title;
      if (el('v4TourText')) el('v4TourText').textContent = step.text;
      if (el('v4TourStepCount')) el('v4TourStepCount').textContent = `Step ${index + 1} of ${activeSteps.length}`;
      if (el('v4TourProgress')) el('v4TourProgress').style.width = `${((index + 1) / activeSteps.length) * 100}%`;
      if (el('v4TourPrev')) el('v4TourPrev').disabled = index === 0;
      if (el('v4TourNext')) el('v4TourNext').textContent = index === activeSteps.length - 1 ? 'Finish' : 'Next';
      placeCard(target);
    }, 220);
  }
  function startTour(){ buildSteps(); index = 0; if (el('v4TourBackdrop')) el('v4TourBackdrop').hidden = false; if (el('v4TourCard')) el('v4TourCard').hidden = false; showStep(); }
  function endTour(){ clearHighlight(); if (el('v4TourBackdrop')) el('v4TourBackdrop').hidden = true; if (el('v4TourCard')) el('v4TourCard').hidden = true; localStorage.setItem('printcraft_v431_tour_seen','1'); }

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('[data-v4-tour-start], [data-v431-tour-start]').forEach(btn => btn.addEventListener('click', startTour));
    el('v4TourClose')?.addEventListener('click', endTour);
    el('v4TourSkip')?.addEventListener('click', endTour);
    el('v4TourPrev')?.addEventListener('click', () => { if (index > 0) { index--; showStep(); } });
    el('v4TourNext')?.addEventListener('click', () => { if (index < activeSteps.length - 1) { index++; showStep(); } else { endTour(); } });
    window.addEventListener('resize', () => { if (!el('v4TourCard')?.hidden) showStep(); });
    if (!localStorage.getItem('printcraft_v431_tour_seen')) setTimeout(startTour, 900);
  });
})();
