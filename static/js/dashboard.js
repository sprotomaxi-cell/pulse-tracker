// Pulse Dashboard

const COLORS = {
    positive: "#4ade80",
    negative: "#f87171",
    neutral: "#6b7280",
    mixed: "#fbbf24",
};

async function fetchJSON(url) {
    const res = await fetch(url);
    return res.json();
}

// ── Overview Cards ──────────────────────────
async function loadOverview() {
    const data = await fetchJSON("/api/overview");
    document.getElementById("total-posts").textContent = data.total_posts;
    document.getElementById("total-analyzed").textContent = data.total_analyzed;
    document.getElementById("positive-count").textContent =
        data.sentiment_distribution.positive || 0;
    document.getElementById("negative-count").textContent =
        data.sentiment_distribution.negative || 0;
}

// ── Trend Chart ─────────────────────────────
async function loadTrendChart() {
    const data = await fetchJSON("/api/trends");
    const days = Object.keys(data).sort();

    const datasets = ["positive", "negative", "neutral", "mixed"].map(
        (sentiment) => ({
            label: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
            data: days.map((d) => data[d]?.[sentiment] || 0),
            borderColor: COLORS[sentiment],
            backgroundColor: COLORS[sentiment] + "20",
            fill: true,
            tension: 0.3,
            pointRadius: 3,
        })
    );

    new Chart(document.getElementById("trend-chart"), {
        type: "line",
        data: {
            labels: days.map((d) => {
                const date = new Date(d + "T00:00:00");
                return date.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                });
            }),
            datasets,
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: "#888", font: { size: 11 } },
                },
            },
            scales: {
                x: {
                    ticks: { color: "#555" },
                    grid: { color: "#1a1a2e" },
                },
                y: {
                    ticks: { color: "#555" },
                    grid: { color: "#1a1a2e" },
                    beginAtZero: true,
                },
            },
        },
    });
}

// ── Topic Sentiment Chart ───────────────────
async function loadTopicChart() {
    const data = await fetchJSON("/api/topic-sentiment");
    const topics = Object.keys(data).slice(0, 10);

    const datasets = ["positive", "negative", "neutral", "mixed"].map(
        (sentiment) => ({
            label: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
            data: topics.map((t) => data[t]?.[sentiment] || 0),
            backgroundColor: COLORS[sentiment] + "cc",
            borderWidth: 0,
        })
    );

    new Chart(document.getElementById("topic-chart"), {
        type: "bar",
        data: {
            labels: topics.map((t) =>
                t.length > 18 ? t.substring(0, 18) + "..." : t
            ),
            datasets,
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: "#888", font: { size: 11 } },
                },
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: { color: "#555", font: { size: 10 } },
                    grid: { display: false },
                },
                y: {
                    stacked: true,
                    ticks: { color: "#555" },
                    grid: { color: "#1a1a2e" },
                    beginAtZero: true,
                },
            },
        },
    });
}

// ── Topics List ─────────────────────────────
async function loadTopics() {
    const data = await fetchJSON("/api/topics");
    const container = document.getElementById("topics-list");
    container.innerHTML = data
        .map(
            (t) =>
                `<span class="topic-tag">${t.name}<span class="count">${t.count}</span></span>`
        )
        .join("");
}

// ── Posts List ───────────────────────────────
async function loadPosts() {
    const data = await fetchJSON("/api/posts");
    const container = document.getElementById("posts-list");

    container.innerHTML = data
        .map((p) => {
            const sub = p.subreddit ? ` r/${p.subreddit}` : "";
            const date = new Date(p.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
            });
            return `
            <div class="post">
                <div class="post-header">
                    <span class="post-source ${p.source}">${p.source}${sub}</span>
                    <span class="sentiment-badge ${p.sentiment}">${p.sentiment}</span>
                    <span class="post-meta">${p.score} pts / ${p.num_comments} comments</span>
                </div>
                <div class="post-title"><a href="${p.url}" target="_blank">${p.title}</a></div>
                <div class="post-summary">${p.summary || ""}</div>
                <div class="post-meta">${date} / ${p.topics.join(", ")}</div>
            </div>`;
        })
        .join("");
}

// ── Init ────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadOverview();
    loadTrendChart();
    loadTopicChart();
    loadTopics();
    loadPosts();
});
