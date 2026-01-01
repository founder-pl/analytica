/**
 * ANALYTICA View Renderer
 * ========================
 * 
 * Renders JSON view specifications to HTML components.
 * Supports: chart, table, card, kpi, grid, dashboard, text, list
 * 
 * Usage:
 *   const renderer = new ViewRenderer(containerElement);
 *   renderer.render(jsonResponse);
 */

export class ViewRenderer {
  constructor(container, options = {}) {
    this.container = typeof container === 'string' 
      ? document.querySelector(container) 
      : container;
    
    this.options = {
      theme: 'light',
      locale: 'pl-PL',
      currency: 'PLN',
      animations: true,
      ...options
    };
    
    this.renderers = {
      chart: this.renderChart.bind(this),
      table: this.renderTable.bind(this),
      card: this.renderCard.bind(this),
      kpi: this.renderKPI.bind(this),
      grid: this.renderGrid.bind(this),
      dashboard: this.renderDashboard.bind(this),
      text: this.renderText.bind(this),
      list: this.renderList.bind(this),
    };
    
    this.colors = [
      '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
      '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1'
    ];
  }

  resolveDataForView(spec, data) {
    if (!spec) return data;
    const path = spec.data_path || spec.dataPath || '';
    if (!path) return data;
    const resolved = this.extractValue(data, path);
    return resolved === undefined ? data : resolved;
  }
  
  /**
   * Main render method - renders complete response with data and views
   */
  render(response) {
    if (!this.container) {
      console.error('ViewRenderer: No container element');
      return;
    }
    
    this.container.innerHTML = '';
    
    // Handle different response formats
    let data = response;
    let views = [];
    
    if (response && typeof response === 'object') {
      if (response.views && Array.isArray(response.views)) {
        data = response.data;
        views = response.views;
      } else if (response.result && response.result.views) {
        data = response.result.data;
        views = response.result.views;
      }
    }
    
    // If no views defined, show raw data
    if (views.length === 0) {
      this.renderRawData(data);
      return;
    }
    
    // Render each view
    const fragment = document.createDocumentFragment();
    for (const viewSpec of views) {
      const element = this.renderView(viewSpec, data);
      if (element) {
        fragment.appendChild(element);
      }
    }
    
    this.container.appendChild(fragment);
  }
  
  /**
   * Render a single view specification
   */
  renderView(spec, data) {
    const renderer = this.renderers[spec.type];
    if (!renderer) {
      console.warn(`ViewRenderer: Unknown view type "${spec.type}"`);
      return this.renderUnknown(spec, data);
    }
    
    try {
      return renderer(spec, data);
    } catch (e) {
      console.error(`ViewRenderer: Error rendering ${spec.type}:`, e);
      return this.renderError(spec, e);
    }
  }
  
  /**
   * Render chart view
   */
  renderChart(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-chart');
    
    const chartArea = document.createElement('div');
    chartArea.className = 'chart-area';
    
    // Simple SVG chart rendering
    const scopedData = this.resolveDataForView(spec, data);
    const chartData = this.extractChartData(spec, scopedData);
    
    if (spec.chart_type === 'bar' || spec.chart_type === 'column') {
      chartArea.appendChild(this.renderBarChart(chartData, spec));
    } else if (spec.chart_type === 'line' || spec.chart_type === 'area') {
      chartArea.appendChild(this.renderLineChart(chartData, spec));
    } else if (spec.chart_type === 'pie' || spec.chart_type === 'donut') {
      chartArea.appendChild(this.renderPieChart(chartData, spec));
    } else if (spec.chart_type === 'gauge') {
      chartArea.appendChild(this.renderGaugeChart(chartData, spec));
    } else {
      // Default to bar
      chartArea.appendChild(this.renderBarChart(chartData, spec));
    }
    
    wrapper.appendChild(chartArea);
    
    // Legend
    if (spec.show_legend && chartData.labels) {
      wrapper.appendChild(this.renderLegend(chartData));
    }
    
    return wrapper;
  }
  
  extractChartData(spec, data) {
    const result = { labels: [], values: [], series: [] };
    
    if (!data) return result;
    
    // Handle array data
    if (Array.isArray(data)) {
      result.labels = data.map(d => d[spec.x_field] || '');
      result.values = data.map(d => parseFloat(d[spec.y_field]) || 0);
      
      // Multiple series
      if (spec.series && spec.series.length > 0) {
        result.series = spec.series.map(field => ({
          name: field,
          values: data.map(d => parseFloat(d[field]) || 0)
        }));
      }
    }
    // Handle object with arrays
    else if (typeof data === 'object') {
      if (data[spec.x_field]) {
        result.labels = Array.isArray(data[spec.x_field]) 
          ? data[spec.x_field] 
          : [data[spec.x_field]];
      }
      if (data[spec.y_field]) {
        result.values = Array.isArray(data[spec.y_field])
          ? data[spec.y_field].map(v => parseFloat(v) || 0)
          : [parseFloat(data[spec.y_field]) || 0];
      }
    }
    
    return result;
  }
  
  renderBarChart(chartData, spec) {
    const width = 400;
    const height = 200;
    const padding = 40;
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('class', 'chart-svg');
    
    if (!chartData.values.length) {
      return this.renderEmptyChart(svg, width, height);
    }
    
    const maxValue = Math.max(...chartData.values, 1);
    const barWidth = (width - padding * 2) / chartData.values.length - 4;
    
    // Grid lines
    if (spec.show_grid !== false) {
      for (let i = 0; i <= 4; i++) {
        const y = padding + (height - padding * 2) * (i / 4);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padding);
        line.setAttribute('x2', width - padding);
        line.setAttribute('y1', y);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', '#e5e7eb');
        line.setAttribute('stroke-width', '1');
        svg.appendChild(line);
      }
    }
    
    // Bars
    chartData.values.forEach((value, i) => {
      const barHeight = (value / maxValue) * (height - padding * 2);
      const x = padding + i * (barWidth + 4);
      const y = height - padding - barHeight;
      
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', y);
      rect.setAttribute('width', barWidth);
      rect.setAttribute('height', barHeight);
      rect.setAttribute('fill', this.colors[i % this.colors.length]);
      rect.setAttribute('rx', '4');
      
      if (this.options.animations) {
        rect.style.animation = `barGrow 0.5s ease-out ${i * 0.1}s both`;
      }
      
      // Tooltip
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = `${chartData.labels[i] || i}: ${this.formatValue(value)}`;
      rect.appendChild(title);
      
      svg.appendChild(rect);
      
      // Label
      if (chartData.labels[i]) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x + barWidth / 2);
        text.setAttribute('y', height - 10);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '10');
        text.setAttribute('fill', '#6b7280');
        text.textContent = this.truncate(String(chartData.labels[i]), 8);
        svg.appendChild(text);
      }
    });
    
    return svg;
  }
  
  renderLineChart(chartData, spec) {
    const width = 400;
    const height = 200;
    const padding = 40;
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('class', 'chart-svg');
    
    if (!chartData.values.length) {
      return this.renderEmptyChart(svg, width, height);
    }
    
    const maxValue = Math.max(...chartData.values, 1);
    const stepX = (width - padding * 2) / (chartData.values.length - 1 || 1);
    
    // Grid
    if (spec.show_grid !== false) {
      for (let i = 0; i <= 4; i++) {
        const y = padding + (height - padding * 2) * (i / 4);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padding);
        line.setAttribute('x2', width - padding);
        line.setAttribute('y1', y);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', '#e5e7eb');
        svg.appendChild(line);
      }
    }
    
    // Line path
    const points = chartData.values.map((value, i) => {
      const x = padding + i * stepX;
      const y = height - padding - (value / maxValue) * (height - padding * 2);
      return `${x},${y}`;
    });
    
    // Area fill
    if (spec.chart_type === 'area') {
      const areaPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const areaD = `M${padding},${height - padding} L${points.join(' L')} L${width - padding},${height - padding} Z`;
      areaPath.setAttribute('d', areaD);
      areaPath.setAttribute('fill', this.colors[0]);
      areaPath.setAttribute('fill-opacity', '0.2');
      svg.appendChild(areaPath);
    }
    
    // Line
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${points.join(' L')}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', this.colors[0]);
    path.setAttribute('stroke-width', '2');
    path.setAttribute('stroke-linecap', 'round');
    svg.appendChild(path);
    
    // Points
    chartData.values.forEach((value, i) => {
      const x = padding + i * stepX;
      const y = height - padding - (value / maxValue) * (height - padding * 2);
      
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', x);
      circle.setAttribute('cy', y);
      circle.setAttribute('r', '4');
      circle.setAttribute('fill', this.colors[0]);
      
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = `${chartData.labels[i] || i}: ${this.formatValue(value)}`;
      circle.appendChild(title);
      
      svg.appendChild(circle);
    });
    
    return svg;
  }
  
  renderPieChart(chartData, spec) {
    const width = 200;
    const height = 200;
    const cx = width / 2;
    const cy = height / 2;
    const radius = 80;
    const innerRadius = spec.chart_type === 'donut' ? 50 : 0;
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('class', 'chart-svg');
    
    if (!chartData.values.length) {
      return this.renderEmptyChart(svg, width, height);
    }
    
    const total = chartData.values.reduce((a, b) => a + b, 0) || 1;
    let currentAngle = -Math.PI / 2;
    
    chartData.values.forEach((value, i) => {
      const sliceAngle = (value / total) * Math.PI * 2;
      const endAngle = currentAngle + sliceAngle;
      
      const x1 = cx + radius * Math.cos(currentAngle);
      const y1 = cy + radius * Math.sin(currentAngle);
      const x2 = cx + radius * Math.cos(endAngle);
      const y2 = cy + radius * Math.sin(endAngle);
      
      const largeArc = sliceAngle > Math.PI ? 1 : 0;
      
      let d;
      if (innerRadius > 0) {
        const ix1 = cx + innerRadius * Math.cos(currentAngle);
        const iy1 = cy + innerRadius * Math.sin(currentAngle);
        const ix2 = cx + innerRadius * Math.cos(endAngle);
        const iy2 = cy + innerRadius * Math.sin(endAngle);
        d = `M${ix1},${iy1} L${x1},${y1} A${radius},${radius} 0 ${largeArc} 1 ${x2},${y2} L${ix2},${iy2} A${innerRadius},${innerRadius} 0 ${largeArc} 0 ${ix1},${iy1}`;
      } else {
        d = `M${cx},${cy} L${x1},${y1} A${radius},${radius} 0 ${largeArc} 1 ${x2},${y2} Z`;
      }
      
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', d);
      path.setAttribute('fill', this.colors[i % this.colors.length]);
      
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      const pct = ((value / total) * 100).toFixed(1);
      title.textContent = `${chartData.labels[i] || i}: ${this.formatValue(value)} (${pct}%)`;
      path.appendChild(title);
      
      svg.appendChild(path);
      currentAngle = endAngle;
    });
    
    return svg;
  }
  
  renderGaugeChart(chartData, spec) {
    const width = 200;
    const height = 120;
    const cx = width / 2;
    const cy = height - 20;
    const radius = 80;
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('class', 'chart-svg');
    
    const value = chartData.values[0] || 0;
    const maxValue = chartData.values[1] || 100;
    const pct = Math.min(value / maxValue, 1);
    
    // Background arc
    const bgPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    bgPath.setAttribute('d', this.describeArc(cx, cy, radius, 180, 360));
    bgPath.setAttribute('fill', 'none');
    bgPath.setAttribute('stroke', '#e5e7eb');
    bgPath.setAttribute('stroke-width', '12');
    svg.appendChild(bgPath);
    
    // Value arc
    const valuePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    valuePath.setAttribute('d', this.describeArc(cx, cy, radius, 180, 180 + pct * 180));
    valuePath.setAttribute('fill', 'none');
    valuePath.setAttribute('stroke', this.getGaugeColor(pct));
    valuePath.setAttribute('stroke-width', '12');
    valuePath.setAttribute('stroke-linecap', 'round');
    svg.appendChild(valuePath);
    
    // Value text
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', cx);
    text.setAttribute('y', cy - 20);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', '24');
    text.setAttribute('font-weight', 'bold');
    text.setAttribute('fill', '#1f2937');
    text.textContent = this.formatValue(value);
    svg.appendChild(text);
    
    return svg;
  }
  
  describeArc(cx, cy, radius, startAngle, endAngle) {
    const start = this.polarToCartesian(cx, cy, radius, endAngle);
    const end = this.polarToCartesian(cx, cy, radius, startAngle);
    const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 0 ${end.x} ${end.y}`;
  }
  
  polarToCartesian(cx, cy, radius, angle) {
    const rad = (angle - 90) * Math.PI / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad)
    };
  }
  
  getGaugeColor(pct) {
    if (pct < 0.5) return '#10b981';
    if (pct < 0.75) return '#f59e0b';
    return '#ef4444';
  }
  
  renderEmptyChart(svg, width, height) {
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', width / 2);
    text.setAttribute('y', height / 2);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', '#9ca3af');
    text.textContent = 'No data';
    svg.appendChild(text);
    return svg;
  }
  
  renderLegend(chartData) {
    const legend = document.createElement('div');
    legend.className = 'chart-legend';
    
    chartData.labels.forEach((label, i) => {
      const item = document.createElement('div');
      item.className = 'legend-item';
      
      const color = document.createElement('span');
      color.className = 'legend-color';
      color.style.backgroundColor = this.colors[i % this.colors.length];
      
      const text = document.createElement('span');
      text.className = 'legend-text';
      text.textContent = label;
      
      item.appendChild(color);
      item.appendChild(text);
      legend.appendChild(item);
    });
    
    return legend;
  }
  
  /**
   * Render table view
   */
  renderTable(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-table');
    
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-wrapper';
    
    const table = document.createElement('table');
    table.className = 'data-table';
    if (spec.striped) table.classList.add('striped');
    
    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    const columns = spec.columns || [];
    columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col.header || col.field;
      if (spec.sortable) {
        th.className = 'sortable';
        th.addEventListener('click', () => this.sortTable(table, col.field));
      }
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Body
    const tbody = document.createElement('tbody');
    const scopedData = this.resolveDataForView(spec, data);
    const rows = Array.isArray(scopedData) ? scopedData : [];
    
    const pageSize = spec.paginate ? spec.page_size : rows.length;
    const displayRows = rows.slice(0, pageSize);
    
    displayRows.forEach(row => {
      const tr = document.createElement('tr');
      columns.forEach(col => {
        const td = document.createElement('td');
        const value = row[col.field];
        td.textContent = this.formatCellValue(value, col);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    
    if (displayRows.length === 0) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = columns.length || 1;
      td.className = 'empty-row';
      td.textContent = 'No data';
      tr.appendChild(td);
      tbody.appendChild(tr);
    }
    
    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    wrapper.appendChild(tableWrapper);
    
    // Pagination info
    if (spec.paginate && rows.length > pageSize) {
      const pagination = document.createElement('div');
      pagination.className = 'table-pagination';
      pagination.textContent = `Showing 1-${pageSize} of ${rows.length}`;
      wrapper.appendChild(pagination);
    }
    
    return wrapper;
  }
  
  sortTable(table, field) {
    // Simple client-side sort (toggle asc/desc)
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const th = Array.from(table.querySelectorAll('th')).find(t => t.textContent.toLowerCase().includes(field.toLowerCase()));
    const isAsc = th && th.classList.contains('sort-asc');
    
    // Clear sort classes
    table.querySelectorAll('th').forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
    
    if (th) {
      th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
    }
    
    // This is a simplified sort - full implementation would need column index
    console.log('Sort by:', field, isAsc ? 'desc' : 'asc');
  }
  
  formatCellValue(value, col) {
    if (value === null || value === undefined) return '-';
    
    if (col.format === 'currency') {
      return this.formatCurrency(value);
    }
    if (col.format === 'percent') {
      return this.formatPercent(value);
    }
    if (col.format === 'number') {
      return this.formatNumber(value);
    }
    if (col.format === 'date') {
      return this.formatDate(value);
    }
    
    return String(value);
  }
  
  /**
   * Render card view
   */
  renderCard(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-card');
    wrapper.classList.add(`card-${spec.style || 'default'}`);
    
    // Icon
    if (spec.icon) {
      const icon = document.createElement('div');
      icon.className = 'card-icon';
      icon.textContent = spec.icon;
      wrapper.appendChild(icon);
    }
    
    // Value
    const value = this.extractValue(data, spec.value_field);
    const valueEl = document.createElement('div');
    valueEl.className = 'card-value';
    valueEl.textContent = this.formatValueByType(value, spec.format);
    wrapper.appendChild(valueEl);
    
    // Trend
    if (spec.trend_field) {
      const trend = this.extractValue(data, spec.trend_field);
      if (trend !== undefined) {
        const trendEl = document.createElement('div');
        trendEl.className = `card-trend ${trend >= 0 ? 'up' : 'down'}`;
        trendEl.textContent = `${trend >= 0 ? '↑' : '↓'} ${Math.abs(trend)}%`;
        wrapper.appendChild(trendEl);
      }
    }
    
    return wrapper;
  }
  
  /**
   * Render KPI view
   */
  renderKPI(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-kpi');
    
    const value = this.extractValue(data, spec.value_field) || 0;
    const target = this.extractValue(data, spec.target_field) || 100;
    const pct = Math.min((value / target) * 100, 100);
    
    // Icon
    if (spec.icon) {
      const icon = document.createElement('div');
      icon.className = 'kpi-icon';
      icon.textContent = spec.icon;
      wrapper.appendChild(icon);
    }
    
    // Values
    const values = document.createElement('div');
    values.className = 'kpi-values';
    
    const current = document.createElement('span');
    current.className = 'kpi-current';
    current.textContent = this.formatValueByType(value, spec.format);
    
    const targetEl = document.createElement('span');
    targetEl.className = 'kpi-target';
    targetEl.textContent = `/ ${this.formatValueByType(target, spec.format)}`;
    
    values.appendChild(current);
    values.appendChild(targetEl);
    wrapper.appendChild(values);
    
    // Progress bar
    if (spec.show_progress) {
      const progress = document.createElement('div');
      progress.className = 'kpi-progress';
      
      const bar = document.createElement('div');
      bar.className = 'kpi-progress-bar';
      bar.style.width = `${pct}%`;
      bar.style.backgroundColor = this.getProgressColor(pct);
      
      progress.appendChild(bar);
      wrapper.appendChild(progress);
      
      const pctLabel = document.createElement('div');
      pctLabel.className = 'kpi-pct';
      pctLabel.textContent = `${pct.toFixed(1)}%`;
      wrapper.appendChild(pctLabel);
    }
    
    return wrapper;
  }
  
  getProgressColor(pct) {
    if (pct >= 100) return '#10b981';
    if (pct >= 75) return '#3b82f6';
    if (pct >= 50) return '#f59e0b';
    return '#ef4444';
  }
  
  /**
   * Render grid layout
   */
  renderGrid(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-grid');
    wrapper.style.gridTemplateColumns = `repeat(${spec.columns || 2}, 1fr)`;
    wrapper.style.gap = `${spec.gap || 16}px`;
    
    if (spec.items && spec.items.length > 0) {
      spec.items.forEach(item => {
        const el = this.renderView(item, data);
        if (el) wrapper.appendChild(el);
      });
    }
    
    return wrapper;
  }
  
  /**
   * Render dashboard
   */
  renderDashboard(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-dashboard');
    
    const widgets = document.createElement('div');
    widgets.className = `dashboard-widgets layout-${spec.layout || 'grid'}`;
    
    if (spec.widgets && spec.widgets.length > 0) {
      spec.widgets.forEach(widget => {
        const el = this.renderView(widget, data);
        if (el) widgets.appendChild(el);
      });
    }
    
    wrapper.appendChild(widgets);
    
    // Refresh indicator
    if (spec.refresh_interval > 0) {
      const refresh = document.createElement('div');
      refresh.className = 'dashboard-refresh';
      refresh.textContent = `Auto-refresh: ${spec.refresh_interval}s`;
      wrapper.appendChild(refresh);
    }
    
    return wrapper;
  }
  
  /**
   * Render text view
   */
  renderText(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-text');
    
    const content = document.createElement('div');
    content.className = 'text-content';
    
    let text = spec.content;
    // Replace {{field}} placeholders with data values
    if (data && typeof text === 'string') {
      text = text.replace(/\{\{(\w+)\}\}/g, (match, field) => {
        return this.extractValue(data, field) ?? match;
      });
    }
    
    if (spec.format === 'markdown') {
      content.innerHTML = this.simpleMarkdown(text);
    } else if (spec.format === 'html') {
      content.innerHTML = text;
    } else {
      content.textContent = text;
    }
    
    wrapper.appendChild(content);
    return wrapper;
  }
  
  simpleMarkdown(text) {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  
  /**
   * Render list view
   */
  renderList(spec, data) {
    const wrapper = this.createWrapper(spec, 'view-list');
    
    const list = document.createElement('ul');
    list.className = 'data-list';
    
    const scopedData = this.resolveDataForView(spec, data);
    const items = Array.isArray(scopedData) ? scopedData : [];
    
    items.forEach(item => {
      const li = document.createElement('li');
      li.className = 'list-item';
      
      if (spec.icon_field && item[spec.icon_field]) {
        const icon = document.createElement('span');
        icon.className = 'list-icon';
        icon.textContent = item[spec.icon_field];
        li.appendChild(icon);
      }
      
      const content = document.createElement('div');
      content.className = 'list-content';
      
      if (spec.primary_field) {
        const primary = document.createElement('div');
        primary.className = 'list-primary';
        primary.textContent = item[spec.primary_field] || '';
        content.appendChild(primary);
      }
      
      if (spec.secondary_field) {
        const secondary = document.createElement('div');
        secondary.className = 'list-secondary';
        secondary.textContent = item[spec.secondary_field] || '';
        content.appendChild(secondary);
      }
      
      li.appendChild(content);
      list.appendChild(li);
    });
    
    if (items.length === 0) {
      const li = document.createElement('li');
      li.className = 'list-empty';
      li.textContent = 'No items';
      list.appendChild(li);
    }
    
    wrapper.appendChild(list);
    return wrapper;
  }
  
  /**
   * Render raw data (fallback)
   */
  renderRawData(data) {
    const pre = document.createElement('pre');
    pre.className = 'view-raw';
    pre.textContent = JSON.stringify(data, null, 2);
    this.container.appendChild(pre);
  }
  
  /**
   * Render unknown view type
   */
  renderUnknown(spec, data) {
    const div = document.createElement('div');
    div.className = 'view-unknown';
    div.innerHTML = `<span class="unknown-type">Unknown view type: ${spec.type}</span>`;
    return div;
  }
  
  /**
   * Render error
   */
  renderError(spec, error) {
    const div = document.createElement('div');
    div.className = 'view-error';
    div.innerHTML = `<span class="error-icon">⚠️</span><span class="error-msg">Error rendering ${spec.type}: ${error.message}</span>`;
    return div;
  }
  
  /**
   * Create view wrapper with title
   */
  createWrapper(spec, className) {
    const wrapper = document.createElement('div');
    wrapper.className = `view-wrapper ${className}`;
    if (spec.id) wrapper.id = spec.id;
    
    if (spec.title) {
      const title = document.createElement('div');
      title.className = 'view-title';
      title.textContent = spec.title;
      wrapper.appendChild(title);
    }
    
    if (spec.description) {
      const desc = document.createElement('div');
      desc.className = 'view-description';
      desc.textContent = spec.description;
      wrapper.appendChild(desc);
    }
    
    return wrapper;
  }
  
  // Utility methods
  
  extractValue(data, field) {
    if (!data || !field) return undefined;
    
    // Handle nested fields like "summary.total"
    const parts = field.split('.');
    let value = data;
    
    for (const part of parts) {
      if (value === null || value === undefined) return undefined;
      value = value[part];
    }
    
    return value;
  }
  
  formatValue(value) {
    if (typeof value === 'number') {
      return value.toLocaleString(this.options.locale);
    }
    return String(value);
  }
  
  formatValueByType(value, format) {
    if (format === 'currency') return this.formatCurrency(value);
    if (format === 'percent') return this.formatPercent(value);
    if (format === 'number') return this.formatNumber(value);
    return this.formatValue(value);
  }
  
  formatCurrency(value) {
    return new Intl.NumberFormat(this.options.locale, {
      style: 'currency',
      currency: this.options.currency
    }).format(value);
  }
  
  formatPercent(value) {
    return new Intl.NumberFormat(this.options.locale, {
      style: 'percent',
      minimumFractionDigits: 1
    }).format(value / 100);
  }
  
  formatNumber(value) {
    return new Intl.NumberFormat(this.options.locale).format(value);
  }
  
  formatDate(value) {
    const date = new Date(value);
    return date.toLocaleDateString(this.options.locale);
  }
  
  truncate(str, len) {
    return str.length > len ? str.slice(0, len) + '…' : str;
  }
}

// CSS styles for views
export const viewStyles = `
/* View Renderer Styles */
.view-wrapper {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 16px;
}

.view-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.view-description {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
}

/* Chart styles */
.view-chart .chart-area {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.chart-svg {
  max-width: 100%;
  height: auto;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

@keyframes barGrow {
  from { transform: scaleY(0); transform-origin: bottom; }
  to { transform: scaleY(1); transform-origin: bottom; }
}

/* Table styles */
.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 10px 12px;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  color: #374151;
}

.data-table th.sortable {
  cursor: pointer;
}

.data-table th.sortable:hover {
  background: #f3f4f6;
}

.data-table th.sort-asc::after { content: ' ↑'; }
.data-table th.sort-desc::after { content: ' ↓'; }

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
}

.data-table.striped tbody tr:nth-child(even) {
  background: #f9fafb;
}

.data-table tbody tr:hover {
  background: #f3f4f6;
}

.empty-row {
  text-align: center;
  color: #9ca3af;
  font-style: italic;
}

.table-pagination {
  padding: 8px 0;
  text-align: right;
  font-size: 12px;
  color: #6b7280;
}

/* Card styles */
.view-card {
  text-align: center;
  padding: 20px;
}

.view-card .card-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.view-card .card-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.view-card .card-trend {
  font-size: 14px;
  margin-top: 4px;
}

.view-card .card-trend.up { color: #10b981; }
.view-card .card-trend.down { color: #ef4444; }

.view-card.card-success { border-left: 4px solid #10b981; }
.view-card.card-warning { border-left: 4px solid #f59e0b; }
.view-card.card-danger { border-left: 4px solid #ef4444; }
.view-card.card-info { border-left: 4px solid #3b82f6; }

/* KPI styles */
.view-kpi {
  text-align: center;
  padding: 20px;
}

.kpi-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.kpi-values {
  margin-bottom: 12px;
}

.kpi-current {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
}

.kpi-target {
  font-size: 14px;
  color: #9ca3af;
}

.kpi-progress {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.kpi-progress-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.kpi-pct {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

/* Grid styles */
.view-grid {
  display: grid;
}

.view-grid > .view-wrapper {
  margin-bottom: 0;
}

/* Dashboard styles */
.dashboard-widgets {
  display: grid;
  gap: 16px;
}

.dashboard-widgets.layout-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.dashboard-widgets.layout-stack {
  grid-template-columns: 1fr;
}

.dashboard-refresh {
  text-align: right;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 8px;
}

/* Text styles */
.view-text .text-content {
  line-height: 1.6;
  color: #374151;
}

/* List styles */
.data-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #e5e7eb;
}

.list-item:last-child {
  border-bottom: none;
}

.list-icon {
  font-size: 20px;
}

.list-primary {
  font-weight: 500;
  color: #1f2937;
}

.list-secondary {
  font-size: 12px;
  color: #6b7280;
}

.list-empty {
  text-align: center;
  color: #9ca3af;
  padding: 20px;
  font-style: italic;
}

/* Raw data */
.view-raw {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
}

/* Error/Unknown */
.view-error, .view-unknown {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 16px;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-unknown {
  background: #fffbeb;
  border-color: #fde68a;
  color: #d97706;
}
`;

// Auto-inject styles
export function injectStyles() {
  if (document.getElementById('view-renderer-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'view-renderer-styles';
  style.textContent = viewStyles;
  document.head.appendChild(style);
}

// Convenience factory
export function createViewRenderer(container, options) {
  injectStyles();
  return new ViewRenderer(container, options);
}
