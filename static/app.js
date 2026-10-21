const $ = (id) => document.getElementById(id);
const fmt = (v) => v === null || v === undefined ? "—" : (typeof v === "number" ? v.toLocaleString("id-ID",{maximumFractionDigits:2}) : v);

function makeChart(title, chart) {
  const card = document.createElement("article");
  card.className = "chart-card";
  const heading = document.createElement("h3");
  heading.textContent = title;
  card.appendChild(heading);
  const bars = document.createElement("div");
  bars.className = "bars";
  const max = Math.max(...chart.values, 1);
  chart.values.forEach((value, i) => {
    const item = document.createElement("div");
    item.className = "bar-item";
    const count = document.createElement("span");
    count.className = "bar-value";
    count.textContent = value;
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${Math.max(3, value / max * 105)}px`;
    bar.title = `${chart.labels[i]}: ${value}`;
    const label = document.createElement("span");
    label.className = "bar-label";
    label.textContent = chart.labels[i];
    label.title = chart.labels[i];
    item.append(count, bar, label);
    bars.appendChild(item);
  });
  card.appendChild(bars);
  const legend = document.createElement("div");
  legend.className = "chart-legend";
  legend.textContent = "Sumbu bawah: nilai/kategori · angka di atas batang: frekuensi";
  card.appendChild(legend);
  return card;
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    const data = await response.json();
    if (!data.loaded) {
      $("error").textContent = data.message;
      $("error").classList.remove("hidden");
      $("filename").textContent = "CSV belum ditemukan";
      $("stats-body").innerHTML = '<tr><td colspan="9">Belum ada data untuk dianalisis.</td></tr>';
      $("chart-grid").innerHTML = '<p>Grafik akan muncul setelah file CSV ditambahkan.</p>';
      return;
    }
    $("rows").textContent = fmt(data.rows);
    $("columns").textContent = fmt(data.columns);
    $("numeric").textContent = fmt(data.numeric_count);
    $("missing").textContent = fmt(data.missing);
    $("filename").textContent = data.filename;

    const body = $("stats-body");
    body.innerHTML = "";
    data.summary.forEach(row => {
      const tr = document.createElement("tr");
      [row.name, row.type, fmt(row.count), fmt(row.mean), fmt(row.median), fmt(row.mode), fmt(row.std), fmt(row.min), fmt(row.max)]
        .forEach(value => { const td = document.createElement("td"); td.textContent = value; tr.appendChild(td); });
      body.appendChild(tr);
    });

    const grid = $("chart-grid");
    grid.innerHTML = "";
    const allCharts = {...data.charts, ...data.category_charts};
    Object.entries(allCharts).forEach(([name, chart]) => grid.appendChild(makeChart(name, chart)));
    if (!Object.keys(allCharts).length) grid.textContent = "Tidak ada kolom yang dapat divisualisasikan.";

    const decisions = $("decisions");
    decisions.innerHTML = "";
    data.decisions.forEach(item => {
      const card = document.createElement("article");
      card.className = "decision";
      const h = document.createElement("h3"); h.textContent = item.title;
      const p = document.createElement("p"); p.textContent = item.detail;
      card.append(h,p); decisions.appendChild(card);
    });
  } catch (error) {
    $("error").textContent = "Dashboard gagal memuat data. Pastikan Flask berjalan dan halaman dibuka melalui http://127.0.0.1:5000.";
    $("error").classList.remove("hidden");
  }
}
loadDashboard();
