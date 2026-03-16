// Pulse Dashboard

const C = {
    green: "#22c55e", red: "#ef4444", amber: "#f59e0b",
    gray: "#94a3b8", blue: "#3b82f6",
};

async function get(url) { return (await fetch(url)).json(); }

// ── Theme Toggle ────────────────────────────
const themeBtn = document.getElementById("theme-btn");
const html = document.documentElement;

function setTheme(theme) {
    html.setAttribute("data-theme", theme);
    localStorage.setItem("pulse-theme", theme);
    themeBtn.textContent = theme === "dark" ? "\u2600" : "\u263E";
    // Rebuild charts with new colors
    if (window._chartsLoaded) location.reload();
}

themeBtn.addEventListener("click", () => {
    setTheme(html.getAttribute("data-theme") === "dark" ? "light" : "dark");
});

// Load saved theme
const saved = localStorage.getItem("pulse-theme");
if (saved) {
    html.setAttribute("data-theme", saved);
    themeBtn.textContent = saved === "dark" ? "\u2600" : "\u263E";
}

// ── Smooth Scroll Nav ───────────────────────
document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
        document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
        item.classList.add("active");
    });
});

// ── Clock ───────────────────────────────────
function tick() {
    document.getElementById("clock").textContent = new Date()
        .toLocaleTimeString("en-US", { hour12: false });
}
setInterval(tick, 1000);
tick();

// ── Chart theme helpers ─────────────────────
function isDark() { return html.getAttribute("data-theme") === "dark"; }
function gridColor() { return isDark() ? "#12151c" : "#f0f1f5"; }
function tickColor() { return isDark() ? "#3a3d48" : "#94a3b8"; }
function tooltipBg() { return isDark() ? "#0c0d12" : "#ffffff"; }
function tooltipText() { return isDark() ? "#d0d2da" : "#1a1d28"; }
function tooltipBorder() { return isDark() ? "#1a1d28" : "#e2e5eb"; }

// ── Metrics ─────────────────────────────────
async function loadOverview() {
    const d = await get("/api/overview");
    const s = d.sentiment_distribution;
    const t = d.total_analyzed || 1;

    document.getElementById("h-total").textContent = d.total_posts + " posts";
    document.getElementById("h-analyzed").textContent = d.total_analyzed + " analyzed";

    [
        ["v-pos", "pct-pos", "f-pos", s.positive || 0],
        ["v-neg", "pct-neg", "f-neg", s.negative || 0],
        ["v-neu", "pct-neu", "f-neu", s.neutral || 0],
        ["v-mix", "pct-mix", "f-mix", s.mixed || 0],
    ].forEach(([v, p, f, val]) => {
        document.getElementById(v).textContent = val;
        document.getElementById(p).textContent = ((val / t) * 100).toFixed(0) + "%";
        document.getElementById(f).style.width = (val / t) * 100 + "%";
    });

    new Chart(document.getElementById("donut-chart"), {
        type: "doughnut",
        data: {
            labels: ["Positive", "Negative", "Neutral", "Mixed"],
            datasets: [{
                data: [s.positive || 0, s.negative || 0, s.neutral || 0, s.mixed || 0],
                backgroundColor: [C.green, C.red, C.gray, C.amber],
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: true, cutout: "68%",
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
        },
    });
}

// ── Sentiment Trend ─────────────────────────
async function loadTrend() {
    const data = await get("/api/trends");
    const days = Object.keys(data).sort();
    const labels = days.map(d => new Date(d + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }));

    const mk = (key, color, fill) => ({
        label: key.charAt(0).toUpperCase() + key.slice(1),
        data: days.map(d => data[d]?.[key] || 0),
        borderColor: color,
        backgroundColor: fill ? color + "18" : "transparent",
        fill,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: tooltipBg(),
        pointBorderColor: color,
        pointBorderWidth: 2,
        pointHoverRadius: 6,
        borderWidth: 2.5,
    });

    new Chart(document.getElementById("trend-chart"), {
        type: "line",
        data: {
            labels,
            datasets: [mk("positive", C.green, true), mk("negative", C.red, true), mk("neutral", C.gray, false), mk("mixed", C.amber, false)],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { position: "top", align: "end", labels: { color: tickColor(), font: { size: 11, family: "'Inter'" }, boxWidth: 12, boxHeight: 3, padding: 10 } },
                tooltip: { backgroundColor: tooltipBg(), titleColor: tooltipText(), bodyColor: tooltipText(), borderColor: tooltipBorder(), borderWidth: 1, padding: 10, bodyFont: { family: "'Inter'", size: 11 } },
            },
            scales: {
                x: { ticks: { color: tickColor(), font: { size: 11 } }, grid: { color: gridColor(), drawBorder: false } },
                y: { ticks: { color: tickColor(), font: { size: 11 }, stepSize: 1 }, grid: { color: gridColor(), drawBorder: false }, beginAtZero: true },
            },
        },
    });
}

// ── Confidence + Volume ─────────────────────
async function loadConf() {
    const data = await get("/api/confidence-trend");
    const labels = data.map(d => new Date(d.day + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }));

    new Chart(document.getElementById("conf-chart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Avg Confidence",
                    data: data.map(d => (d.confidence * 100).toFixed(0)),
                    borderColor: C.blue, backgroundColor: C.blue + "15", fill: true,
                    tension: 0.4, pointRadius: 4, pointBackgroundColor: tooltipBg(),
                    pointBorderColor: C.blue, pointBorderWidth: 2, borderWidth: 2.5, yAxisID: "y",
                },
                {
                    label: "Volume",
                    data: data.map(d => d.volume),
                    borderColor: C.amber, backgroundColor: "transparent",
                    borderWidth: 2, borderDash: [4, 3], tension: 0.4,
                    pointRadius: 3, pointBackgroundColor: C.amber, pointBorderWidth: 0, yAxisID: "y1",
                },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { position: "top", align: "end", labels: { color: tickColor(), font: { size: 11, family: "'Inter'" }, boxWidth: 12, boxHeight: 3, padding: 10 } },
                tooltip: { backgroundColor: tooltipBg(), titleColor: tooltipText(), bodyColor: tooltipText(), borderColor: tooltipBorder(), borderWidth: 1, padding: 10 },
            },
            scales: {
                x: { ticks: { color: tickColor(), font: { size: 11 } }, grid: { color: gridColor(), drawBorder: false } },
                y: { position: "left", ticks: { color: C.blue, font: { size: 10 }, callback: v => v + "%" }, grid: { color: gridColor(), drawBorder: false }, min: 0, max: 100 },
                y1: { position: "right", ticks: { color: C.amber, font: { size: 10 }, stepSize: 1 }, grid: { display: false }, beginAtZero: true },
            },
        },
    });
}

// ── Topic Chart ─────────────────────────────
async function loadTopicChart() {
    const data = await get("/api/topic-sentiment");
    const topics = Object.keys(data).slice(0, 8);
    const mk = (key, color) => ({
        label: key, data: topics.map(t => data[t]?.[key] || 0),
        backgroundColor: color + "cc", borderWidth: 0, borderRadius: 3, barThickness: 14,
    });

    new Chart(document.getElementById("topic-chart"), {
        type: "bar",
        data: {
            labels: topics.map(t => t.length > 16 ? t.slice(0, 16) + ".." : t),
            datasets: [mk("positive", C.green), mk("negative", C.red), mk("neutral", C.gray), mk("mixed", C.amber)],
        },
        options: {
            responsive: true, maintainAspectRatio: false, indexAxis: "y",
            plugins: { legend: { display: false } },
            scales: {
                x: { stacked: true, ticks: { color: tickColor(), font: { size: 10 }, stepSize: 1 }, grid: { color: gridColor() }, beginAtZero: true },
                y: { stacked: true, ticks: { color: tickColor(), font: { size: 11, family: "'Inter'" } }, grid: { display: false } },
            },
        },
    });
}

// ── Topics List ─────────────────────────────
async function loadTopics() {
    const data = await get("/api/topics");
    const el = document.getElementById("topics-grid");
    const mx = data.length > 0 ? data[0].count : 1;
    document.getElementById("t-count").textContent = data.length + " topics";

    el.innerHTML = data.map(t => `
        <div class="topic-row">
            <span class="topic-name">${t.name}</span>
            <div class="topic-bar-wrap">
                <div class="topic-bar"><div class="topic-bar-fill" style="width:${(t.count / mx) * 100}%"></div></div>
                <span class="topic-count">${t.count}</span>
            </div>
        </div>`).join("");
}

// ── Feed ────────────────────────────────────
async function loadPosts() {
    const data = await get("/api/posts");
    const el = document.getElementById("feed");
    document.getElementById("f-count").textContent = data.length + " posts";

    el.innerHTML = data.map(p => {
        const time = new Date(p.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false });
        const sub = p.subreddit ? ` r/${p.subreddit}` : "";
        const topics = p.topics.map(t => `<span>${t}</span>`).join(" \u00b7 ");

        let thumb = '<span class="fi">&#9632;</span>';
        if (p.url && p.url.startsWith("http")) {
            try {
                const host = new URL(p.url).hostname;
                thumb = `<img src="https://www.google.com/s2/favicons?domain=${host}&sz=128" onerror="this.parentElement.innerHTML='<span class=fi>&#9632;</span>'" alt="">`;
            } catch (e) {}
        }

        return `
        <div class="post-card">
            <div class="post-thumb">${thumb}</div>
            <div class="post-content">
                <div class="post-meta">
                    <span class="post-time">${time}</span>
                    <span class="src ${p.source}">${p.source.toUpperCase()}${sub}</span>
                    <span class="sent ${p.sentiment}">${p.sentiment.toUpperCase()}</span>
                    <span class="post-pts">${p.score}pts \u00b7 ${p.num_comments}cmt</span>
                </div>
                <div class="post-title"><a href="${p.url}" target="_blank">${p.title}</a></div>
                <div class="post-sum">${p.summary || ""}</div>
                <div class="post-tags">${topics}</div>
            </div>
        </div>`;
    }).join("");
}

// ── Init ────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadOverview();
    loadTrend();
    loadConf();
    loadTopicChart();
    loadTopics();
    loadPosts();
    window._chartsLoaded = true;
});
