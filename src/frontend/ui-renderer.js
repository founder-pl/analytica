/**
 * ANALYTICA UI Renderer
 * =====================
 * Renders UI components from DSL specifications
 */

export class UIRenderer {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      theme: 'light',
      baseUrl: window.location.origin,
      ...options
    };
    this.components = {};
    this.eventHandlers = {};
  }

  /**
   * Render UI spec to container
   */
  render(spec) {
    if (!spec) return;
    
    const ui = spec.ui || [];
    const data = spec.data || {};
    
    let html = '';
    for (const component of ui) {
      html += this.renderComponent(component, data);
    }
    
    this.container.innerHTML = html;
    this.bindEvents();
  }

  /**
   * Render single component
   */
  renderComponent(spec, data) {
    const renderer = this[`render_${spec.type}`];
    if (renderer) {
      return renderer.call(this, spec, data);
    }
    console.warn(`Unknown UI component type: ${spec.type}`);
    return `<div class="ui-unknown">[Unknown: ${spec.type}]</div>`;
  }

  /**
   * Render page container
   */
  render_page(spec, data) {
    return `
      <div class="ui-page ui-page--${spec.layout}" data-theme="${spec.theme}">
        <title>${spec.title}</title>
      </div>
    `;
  }

  /**
   * Render navigation
   */
  render_nav(spec, data) {
    const links = (spec.links || []).map(link => 
      `<li><a href="${link.href || '#'}">${link.text}</a></li>`
    ).join('');
    
    const cta = (spec.cta || []).map(btn =>
      `<a href="${btn.href || '#'}" class="btn btn-${btn.variant || 'primary'}">${btn.text}</a>`
    ).join('');
    
    return `
      <nav class="nav ${spec.sticky ? 'nav--sticky' : ''}">
        <div class="container">
          <a href="/" class="nav-logo">
            ${spec.logo ? `<img src="${spec.logo}" alt="${spec.brand}">` : ''}
            <span>${spec.brand}</span>
          </a>
          <ul class="nav-links">${links}</ul>
          <div class="nav-cta">${cta}</div>
        </div>
      </nav>
    `;
  }

  /**
   * Render hero section
   */
  render_hero(spec, data) {
    const ctaPrimary = spec.cta_primary?.text ? 
      `<a href="${spec.cta_primary.href || '#'}" class="btn btn-primary btn-lg">${spec.cta_primary.text}</a>` : '';
    const ctaSecondary = spec.cta_secondary?.text ?
      `<a href="${spec.cta_secondary.href || '#'}" class="btn btn-ghost btn-lg">${spec.cta_secondary.text}</a>` : '';
    
    return `
      <section class="hero ${spec.gradient ? 'hero--gradient' : ''}">
        <div class="container">
          <div class="hero-content">
            ${spec.badge ? `<div class="hero-badge">${spec.badge}</div>` : ''}
            <h1 class="hero-title">${spec.title}</h1>
            ${spec.subtitle ? `<p class="hero-subtitle">${spec.subtitle}</p>` : ''}
            <div class="hero-cta">
              ${ctaPrimary}
              ${ctaSecondary}
            </div>
          </div>
          ${spec.image ? `<div class="hero-image"><img src="${spec.image}" alt=""></div>` : ''}
        </div>
      </section>
    `;
  }

  /**
   * Render section
   */
  render_section(spec, data) {
    const children = (spec.children || []).map(child => 
      this.renderComponent(child, data)
    ).join('');
    
    return `
      <section class="section section--${spec.layout} section--bg-${spec.background} section--pad-${spec.padding}" id="${spec.id}">
        <div class="container">
          ${spec.title ? `<h2 class="section-title">${spec.title}</h2>` : ''}
          ${spec.subtitle ? `<p class="section-subtitle">${spec.subtitle}</p>` : ''}
          <div class="section-content">
            ${children}
          </div>
        </div>
      </section>
    `;
  }

  /**
   * Render grid
   */
  render_grid(spec, data) {
    const items = (spec.items || []).map(item => {
      if (typeof item === 'object' && item.type) {
        return `<div class="grid-item">${this.renderComponent(item, data)}</div>`;
      }
      return `<div class="grid-item">${item}</div>`;
    }).join('');
    
    return `
      <div class="ui-grid ui-grid--${spec.columns}col ui-grid--gap-${spec.gap}">
        ${items}
      </div>
    `;
  }

  /**
   * Render form
   */
  render_form(spec, data) {
    const fields = (spec.fields || []).map(field => 
      this.renderFormField(field, data)
    ).join('');
    
    return `
      <form class="ui-form ui-form--${spec.layout}" action="${spec.action}" method="${spec.method}" id="${spec.id}">
        ${fields}
        <div class="form-actions">
          <button type="submit" class="btn btn-primary">${spec.submit_text}</button>
        </div>
      </form>
    `;
  }

  /**
   * Render form field
   */
  renderFormField(field, data) {
    const value = data[field.name] || '';
    const required = field.required ? 'required' : '';
    
    let input = '';
    switch (field.input_type) {
      case 'textarea':
        input = `<textarea name="${field.name}" class="form-input" placeholder="${field.placeholder || ''}" ${required}>${value}</textarea>`;
        break;
      case 'select':
        const options = (field.options || []).map(opt => 
          `<option value="${opt.value || opt}" ${opt.value === value ? 'selected' : ''}>${opt.label || opt}</option>`
        ).join('');
        input = `<select name="${field.name}" class="form-input" ${required}><option value="">Wybierz...</option>${options}</select>`;
        break;
      case 'checkbox':
        input = `<input type="checkbox" name="${field.name}" class="form-checkbox" ${value ? 'checked' : ''} ${required}>`;
        break;
      default:
        input = `<input type="${field.input_type || 'text'}" name="${field.name}" class="form-input" placeholder="${field.placeholder || ''}" value="${value}" ${required}>`;
    }
    
    return `
      <div class="form-group">
        <label class="form-label">${field.label}${field.required ? ' *' : ''}</label>
        ${input}
      </div>
    `;
  }

  /**
   * Render input (standalone)
   */
  render_input(spec, data) {
    return this.renderFormField(spec, data);
  }

  /**
   * Render button
   */
  render_button(spec, data) {
    const icon = spec.icon ? `<span class="btn-icon">${spec.icon}</span>` : '';
    
    if (spec.href) {
      return `<a href="${spec.href}" class="btn btn-${spec.variant} btn-${spec.size}">${icon}${spec.text}</a>`;
    }
    
    return `<button type="button" class="btn btn-${spec.variant} btn-${spec.size}" data-onclick="${spec.onclick}">${icon}${spec.text}</button>`;
  }

  /**
   * Render stats section
   */
  render_stats(spec, data) {
    const items = (spec.items || []).map(item => `
      <div class="stat-item">
        ${item.icon ? `<span class="stat-icon">${item.icon}</span>` : ''}
        <div class="stat-value">${this.formatValue(item.value, data)}</div>
        <div class="stat-label">${item.label}</div>
        ${item.trend ? `<div class="stat-trend stat-trend--${item.trend > 0 ? 'up' : 'down'}">${item.trend > 0 ? '↑' : '↓'} ${Math.abs(item.trend)}%</div>` : ''}
      </div>
    `).join('');
    
    return `
      <div class="ui-stats ui-stats--${spec.layout}">
        ${items}
      </div>
    `;
  }

  /**
   * Render pricing table
   */
  render_pricing(spec, data) {
    const plans = (spec.plans || []).map(plan => {
      const features = (plan.features || []).map(f => `<li>${f}</li>`).join('');
      const isHighlight = plan.id === spec.highlight || plan.highlight;
      
      return `
        <div class="pricing-card ${isHighlight ? 'pricing-card--highlight' : ''}">
          ${plan.badge ? `<div class="pricing-badge">${plan.badge}</div>` : ''}
          <h3 class="pricing-name">${plan.name}</h3>
          <div class="pricing-price">
            ${plan.price}<span>${plan.period || '/mies.'}</span>
          </div>
          <ul class="pricing-features">${features}</ul>
          <a href="${plan.cta?.href || '#'}" class="btn btn-${isHighlight ? 'primary' : 'secondary'}">${plan.cta?.text || 'Wybierz'}</a>
        </div>
      `;
    }).join('');
    
    return `
      <div class="ui-pricing">
        ${plans}
      </div>
    `;
  }

  /**
   * Render features grid
   */
  render_features(spec, data) {
    const items = (spec.items || []).map(item => `
      <div class="feature-card">
        ${item.icon ? `<div class="feature-icon">${item.icon}</div>` : ''}
        <h3 class="feature-title">${item.title}</h3>
        <p class="feature-desc">${item.description || ''}</p>
      </div>
    `).join('');
    
    return `
      <div class="ui-features ui-features--${spec.columns}col">
        ${items}
      </div>
    `;
  }

  /**
   * Render footer
   */
  render_footer(spec, data) {
    const linkGroups = (spec.links || []).map(group => {
      const links = (group.items || []).map(link => 
        `<li><a href="${link.href || '#'}">${link.text}</a></li>`
      ).join('');
      return `
        <div class="footer-group">
          <h4>${group.title}</h4>
          <ul>${links}</ul>
        </div>
      `;
    }).join('');
    
    const social = (spec.social || []).map(s => 
      `<a href="${s.href}" class="social-link">${s.icon || s.name}</a>`
    ).join('');
    
    return `
      <footer class="ui-footer">
        <div class="container">
          <div class="footer-brand">
            <span>${spec.brand}</span>
          </div>
          <div class="footer-links">${linkGroups}</div>
          <div class="footer-social">${social}</div>
          <div class="footer-copyright">${spec.copyright}</div>
        </div>
      </footer>
    `;
  }

  /**
   * Format value from data
   */
  formatValue(value, data) {
    if (typeof value === 'string' && value.startsWith('$')) {
      const field = value.slice(1);
      return data[field] !== undefined ? data[field] : value;
    }
    return value;
  }

  /**
   * Bind event handlers
   */
  bindEvents() {
    this.container.querySelectorAll('[data-onclick]').forEach(el => {
      const handler = el.dataset.onclick;
      el.addEventListener('click', () => {
        if (this.eventHandlers[handler]) {
          this.eventHandlers[handler](el);
        } else if (typeof window[handler] === 'function') {
          window[handler](el);
        }
      });
    });
    
    this.container.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => this.handleFormSubmit(e, form));
    });
  }

  /**
   * Handle form submission
   */
  async handleFormSubmit(e, form) {
    e.preventDefault();
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const action = form.action || `${this.options.baseUrl}/api/v1/forms/submit`;
    
    try {
      const response = await fetch(action, {
        method: form.method || 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        this.showMessage(form, 'success', result.message || 'Wysłano pomyślnie!');
        form.reset();
      } else {
        this.showMessage(form, 'error', result.message || 'Wystąpił błąd');
      }
    } catch (err) {
      this.showMessage(form, 'error', 'Błąd połączenia z serwerem');
    }
  }

  /**
   * Show message
   */
  showMessage(target, type, message) {
    const existing = target.querySelector('.ui-message');
    if (existing) existing.remove();
    
    const el = document.createElement('div');
    el.className = `ui-message ui-message--${type}`;
    el.textContent = message;
    target.insertBefore(el, target.firstChild);
    
    setTimeout(() => el.remove(), 5000);
  }

  /**
   * Register event handler
   */
  on(event, handler) {
    this.eventHandlers[event] = handler;
  }
}

/**
 * Create UI renderer instance
 */
export function createUIRenderer(container, options = {}) {
  return new UIRenderer(container, options);
}

/**
 * Inject UI renderer styles
 */
export function injectUIStyles() {
  if (document.getElementById('ui-renderer-styles')) return;
  
  const styles = document.createElement('style');
  styles.id = 'ui-renderer-styles';
  styles.textContent = `
    /* UI Renderer Base Styles */
    .ui-page { min-height: 100vh; }
    
    /* Grid */
    .ui-grid { display: grid; gap: 24px; }
    .ui-grid--2col { grid-template-columns: repeat(2, 1fr); }
    .ui-grid--3col { grid-template-columns: repeat(3, 1fr); }
    .ui-grid--4col { grid-template-columns: repeat(4, 1fr); }
    .ui-grid--gap-sm { gap: 12px; }
    .ui-grid--gap-md { gap: 24px; }
    .ui-grid--gap-lg { gap: 32px; }
    
    /* Stats */
    .ui-stats { display: flex; gap: 32px; }
    .ui-stats--vertical { flex-direction: column; }
    .stat-item { text-align: center; }
    .stat-icon { font-size: 2rem; margin-bottom: 8px; }
    .stat-value { font-size: 2.5rem; font-weight: 700; }
    .stat-label { color: var(--muted); font-size: 0.9rem; }
    .stat-trend { font-size: 0.85rem; margin-top: 4px; }
    .stat-trend--up { color: #10b981; }
    .stat-trend--down { color: #ef4444; }
    
    /* Pricing */
    .ui-pricing { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
    .pricing-card { background: white; border-radius: 12px; padding: 32px; border: 2px solid var(--border); text-align: center; position: relative; }
    .pricing-card--highlight { border-color: var(--primary); box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15); }
    .pricing-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--primary); color: white; padding: 4px 16px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .pricing-name { font-size: 1.25rem; margin-bottom: 16px; }
    .pricing-price { font-size: 2.5rem; font-weight: 700; margin-bottom: 24px; }
    .pricing-price span { font-size: 1rem; color: var(--muted); font-weight: 400; }
    .pricing-features { list-style: none; padding: 0; margin: 0 0 24px; text-align: left; }
    .pricing-features li { padding: 8px 0; border-bottom: 1px solid var(--border); }
    
    /* Features */
    .ui-features { display: grid; gap: 24px; }
    .ui-features--2col { grid-template-columns: repeat(2, 1fr); }
    .ui-features--3col { grid-template-columns: repeat(3, 1fr); }
    .ui-features--4col { grid-template-columns: repeat(4, 1fr); }
    .feature-card { background: white; border-radius: 12px; padding: 24px; border: 1px solid var(--border); }
    .feature-icon { font-size: 2rem; margin-bottom: 12px; }
    .feature-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 8px; }
    .feature-desc { color: var(--muted); font-size: 0.9rem; }
    
    /* Footer */
    .ui-footer { background: #1a1a2e; color: white; padding: 48px 0 24px; margin-top: 64px; }
    .ui-footer .container { display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 32px; }
    .footer-links { display: flex; gap: 48px; }
    .footer-group h4 { font-size: 0.9rem; margin-bottom: 16px; opacity: 0.7; }
    .footer-group ul { list-style: none; padding: 0; margin: 0; }
    .footer-group li { margin-bottom: 8px; }
    .footer-group a { color: white; text-decoration: none; opacity: 0.8; }
    .footer-group a:hover { opacity: 1; }
    .footer-copyright { grid-column: 1 / -1; text-align: center; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.1); opacity: 0.6; font-size: 0.85rem; }
    
    /* Form */
    .ui-form { max-width: 500px; }
    .ui-form--horizontal .form-group { display: flex; align-items: center; gap: 16px; }
    .ui-form--horizontal .form-label { width: 120px; flex-shrink: 0; }
    
    /* Message */
    .ui-message { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 0.9rem; }
    .ui-message--success { background: #d1fae5; color: #059669; }
    .ui-message--error { background: #fee2e2; color: #dc2626; }
    
    /* Responsive */
    @media (max-width: 768px) {
      .ui-grid--3col, .ui-grid--4col { grid-template-columns: repeat(2, 1fr); }
      .ui-features--3col, .ui-features--4col { grid-template-columns: 1fr; }
      .ui-stats { flex-wrap: wrap; justify-content: center; }
      .ui-footer .container { grid-template-columns: 1fr; }
      .footer-links { flex-direction: column; gap: 24px; }
    }
  `;
  
  document.head.appendChild(styles);
}
