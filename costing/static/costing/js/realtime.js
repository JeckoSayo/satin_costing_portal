(function () {
  const sockets = new Map();
  const reconnectTimers = new Map();
  const maxDelay = 30000;

  function wsUrl(path) {
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    return `${scheme}://${window.location.host}${path}`;
  }

  function peso(value) {
    return `₱${Number(value || 0).toFixed(2)}`;
  }

  function setText(selector, value) {
    document.querySelectorAll(selector).forEach((element) => {
      element.textContent = value;
    });
  }

  function showToast(title, message, level) {
    const container = document.querySelector("[data-realtime-toasts]");
    if (!container || !window.bootstrap) {
      return;
    }

    const toast = document.createElement("div");
    toast.className = "toast border-0 shadow";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    toast.setAttribute("aria-atomic", "true");
    toast.innerHTML = `
      <div class="toast-header">
        <span class="rounded-circle me-2 bg-${level === "warning" ? "warning" : level === "success" ? "success" : "primary"}" style="width:.75rem;height:.75rem;"></span>
        <strong class="me-auto">${escapeHtml(title || "Notification")}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">${escapeHtml(message || "")}</div>
    `;
    container.prepend(toast);
    new window.bootstrap.Toast(toast, { delay: 6000 }).show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function updateDashboard(payload) {
    setText("[data-realtime='today-revenue']", peso(payload.today_revenue));
    setText("[data-realtime='today-profit']", peso(payload.today_profit));
    setText("[data-realtime='today-orders']", payload.today_orders || 0);
    setText("[data-realtime='due-today-count']", payload.due_today_count || 0);
    setText("[data-realtime='ready-count']", payload.ready_count || 0);
    setText("[data-realtime='unpaid-balance']", peso(payload.unpaid_balance));
    setText("[data-realtime='low-stock-count']", payload.low_stock_count || 0);

    const lowStockList = document.querySelector("[data-realtime-low-stock-list]");
    if (lowStockList && Array.isArray(payload.low_stock_materials)) {
      lowStockList.innerHTML = payload.low_stock_materials.length
        ? payload.low_stock_materials.map((material) => `
          <div>
            <span>${escapeHtml(material.item_name).slice(0, 30)}</span>
            <strong>${Number(material.stock_qty || 0).toFixed(2)} ${escapeHtml(material.unit)}</strong>
          </div>
        `).join("")
        : `<div class="v42-empty"><i class="bi bi-check-circle"></i>No low-stock materials right now.</div>`;
    }

    updateRecentSales(payload.recent_sales);
    updateRevenueChart(payload.charts);
  }

  function updateRecentSales(sales) {
    const body = document.querySelector("[data-realtime-recent-sales]");
    if (!body || !Array.isArray(sales)) {
      return;
    }

    body.innerHTML = sales.slice(0, 5).map((sale) => `
      <tr>
        <td>${escapeHtml(sale.customer_name || "Walk-in").slice(0, 20)}</td>
        <td>${escapeHtml(sale.order_name || "").slice(0, 28)}</td>
        <td class="text-end">${peso(sale.selling_price)}</td>
        <td><span class="badge rounded-pill text-bg-light">${escapeHtml(sale.status)}</span></td>
      </tr>
    `).join("") || `<tr><td colspan="4" class="text-muted text-center py-4">No sales logged yet.</td></tr>`;
  }

  function updateRevenueChart(charts) {
    if (!charts || !window.revenueProfitChart) {
      return;
    }

    window.revenueProfitChart.data.labels = charts.labels || [];
    window.revenueProfitChart.data.datasets[0].data = charts.revenue || [];
    window.revenueProfitChart.data.datasets[1].data = charts.cost || [];
    window.revenueProfitChart.data.datasets[2].data = charts.profit || [];
    window.revenueProfitChart.update();
  }

  function updateInventory(payload) {
    setText("[data-realtime='low-stock-count']", payload.low_stock_count || 0);
    if (payload.material) {
      updateMaterialRow(payload.material);
    }
  }

  function updateMaterialRow(material) {
    const row = document.querySelector(`[data-material-id='${material.id}']`);
    if (!row) {
      return;
    }

    const stock = row.querySelector("[data-material-stock]");
    const unitCost = row.querySelector("[data-material-unit-cost]");
    const basis = row.querySelector("[data-material-basis]");
    const status = row.querySelector("[data-material-stock-status]");
    if (stock) stock.textContent = Number(material.stock_qty || 0).toFixed(0);
    if (unitCost) unitCost.textContent = peso(material.unit_cost);
    if (basis) basis.textContent = material.costing_basis_label || "";
    if (status) {
      status.innerHTML = material.stock_qty <= 0
        ? `<span class="materials-badge red">Out</span>`
        : material.is_low_stock
          ? `<span class="materials-badge yellow">Low</span>`
          : "";
    }
  }

  function updateSales(payload) {
    setText("[data-realtime='sales-total-orders']", payload.total_orders || 0);
    setText("[data-realtime='sales-total-sales']", peso(payload.total_sales));
    setText("[data-realtime='sales-total-cost']", peso(payload.total_cost));
    setText("[data-realtime='sales-total-profit']", peso(payload.total_profit));
  }

  function handleMessage(namespace, data) {
    if (data.type === "notification") {
      showToast(data.payload.title, data.payload.message, data.payload.level);
      return;
    }

    if (namespace === "dashboard" && data.payload) updateDashboard(data.payload);
    if (namespace === "inventory" && data.payload) updateInventory(data.payload);
    if (namespace === "sales" && data.payload) updateSales(data.payload);
  }

  function connect(namespace, path, attempt) {
    const socket = new WebSocket(wsUrl(path));
    sockets.set(namespace, socket);

    socket.onmessage = (event) => {
      try {
        handleMessage(namespace, JSON.parse(event.data));
      } catch (error) {
        console.warn("Invalid realtime message", error);
      }
    };

    socket.onclose = (event) => {
      sockets.delete(namespace);
      if (event.code === 4401) {
        return;
      }
      const delay = Math.min(1000 * 2 ** attempt, maxDelay);
      reconnectTimers.set(namespace, window.setTimeout(() => connect(namespace, path, attempt + 1), delay));
    };

    socket.onerror = () => socket.close();
  }

  document.addEventListener("DOMContentLoaded", () => {
    connect("dashboard", "/ws/dashboard/", 0);
    connect("notifications", "/ws/notifications/", 0);
    connect("inventory", "/ws/inventory/", 0);
    connect("sales", "/ws/sales/", 0);
  });

  window.SatinRealtime = {
    sockets,
    reconnectTimers,
    showToast,
  };
})();
