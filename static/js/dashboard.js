const C = { green: "#22c55e", red: "#ef4444", amber: "#f59e0b", gray: "#94a3b8", blue: "#3b82f6", purple: "#8b5cf6" };
const get = async u => (await fetch(u)).json();
const isDark = () => document.documentElement.getAttribute("data-theme") === "dark";
const gc = () => isDark() ? "#10131a" : "#eceef2";
const tc = () => isDark() ? "#3a3d48" : "#94a3b8";
const tbg = () => isDark() ? "#0b0c10" : "#fff";
const ttx = () => isDark() ? "#cdd0d8" : "#1a1d28";
const tbd = () => isDark() ? "#181b24" : "#d0d4dc";

// ── Theme ───────────────────────────────────
const btn = document.getElementById("theme-btn");
const html = document.documentElement;
function setTheme(t) { html.setAttribute("data-theme", t); localStorage.setItem("pulse-theme", t); btn.textContent = t === "dark" ? "\u2600" : "\u263E"; }
btn.addEventListener("click", () => { setTheme(isDark() ? "light" : "dark"); location.reload(); });
const sv = localStorage.getItem("pulse-theme");
if (sv) { html.setAttribute("data-theme", sv); btn.textContent = sv === "dark" ? "\u2600" : "\u263E"; }

// ── Sidebar nav ─────────────────────────────
document.querySelectorAll(".sb-item[data-target]").forEach(el => {
    el.addEventListener("click", e => {
        document.querySelectorAll(".sb-item").forEach(i => i.classList.remove("active"));
        el.classList.add("active");
    });
});

// ── Clock ───────────────────────────────────
setInterval(() => { document.getElementById("clock").textContent = new Date().toLocaleTimeString("en-US", { hour12: false }); }, 1000);
document.getElementById("clock").textContent = new Date().toLocaleTimeString("en-US", { hour12: false });

// ── Overview ────────────────────────────────
async function loadOverview() {
    const d = await get("/api/overview");
    const s = d.sentiment_distribution;
    const t = d.total_analyzed || 1;

    document.getElementById("h-total").textContent = d.total_posts + " posts";
    document.getElementById("h-analyzed").textContent = d.total_analyzed + " analyzed";

    [["v-pos","pct-pos","f-pos",s.positive||0],["v-neg","pct-neg","f-neg",s.negative||0],
     ["v-neu","pct-neu","f-neu",s.neutral||0],["v-mix","pct-mix","f-mix",s.mixed||0]
    ].forEach(([v,p,f,val]) => {
        document.getElementById(v).textContent = val;
        document.getElementById(p).textContent = ((val/t)*100).toFixed(0)+"%";
        document.getElementById(f).style.width = (val/t)*100+"%";
    });

    // Stats table
    const tbl = document.getElementById("stats-tbl");
    const rows = [
        ["Total", d.total_posts], ["Analyzed", d.total_analyzed],
        ...Object.entries(d.sources).map(([k,v]) => [k.toUpperCase(), v]),
        ["Pos Rate", ((s.positive||0)/t*100).toFixed(0)+"%"],
    ];
    tbl.innerHTML = rows.map(([l,v]) => `<tr><td class="lbl">${l}</td><td class="val">${v}</td></tr>`).join("");

    // Donut
    new Chart(document.getElementById("donut-chart"), {
        type: "doughnut",
        data: { datasets: [{ data: [s.positive||0,s.negative||0,s.neutral||0,s.mixed||0], backgroundColor: [C.green,C.red,C.gray,C.amber], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: true, cutout: "65%", plugins: { legend: { display: false }, tooltip: { enabled: false } } },
    });

    // Source distribution pie
    new Chart(document.getElementById("source-chart"), {
        type: "doughnut",
        data: {
            labels: Object.keys(d.sources),
            datasets: [{ data: Object.values(d.sources), backgroundColor: [C.blue, C.amber, C.green, C.purple, C.red], borderWidth: 0 }],
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: "50%",
            plugins: {
                legend: { position: "right", labels: { color: tc(), font: { size: 10, family: "'Inter'" }, boxWidth: 8, padding: 6 } },
                tooltip: { backgroundColor: tbg(), titleColor: ttx(), bodyColor: ttx(), borderColor: tbd(), borderWidth: 1, bodyFont: { size: 10 }, padding: 6 },
            },
        },
    });

    return { sources: d.sources, sentiments: s };
}

// ── Trend ───────────────────────────────────
async function loadTrend() {
    const data = await get("/api/trends");
    const days = Object.keys(data).sort();
    const labels = days.map(d => new Date(d+"T00:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric"}));
    const mk = (k,c,f) => ({ label:k[0].toUpperCase()+k.slice(1), data:days.map(d=>data[d]?.[k]||0), borderColor:c, backgroundColor:f?c+"15":"transparent", fill:f, tension:.4, pointRadius:3, pointBackgroundColor:tbg(), pointBorderColor:c, pointBorderWidth:2, borderWidth:2 });

    new Chart(document.getElementById("trend-chart"), {
        type: "line",
        data: { labels, datasets: [mk("positive",C.green,true),mk("negative",C.red,true),mk("neutral",C.gray,false),mk("mixed",C.amber,false)] },
        options: {
            responsive:true, maintainAspectRatio:false, interaction:{mode:"index",intersect:false},
            plugins: {
                legend:{position:"top",align:"end",labels:{color:tc(),font:{size:9,family:"'Inter'"},boxWidth:10,boxHeight:2,padding:8}},
                tooltip:{backgroundColor:tbg(),titleColor:ttx(),bodyColor:ttx(),borderColor:tbd(),borderWidth:1,padding:6,bodyFont:{size:10}},
            },
            scales: {
                x:{ticks:{color:tc(),font:{size:9}},grid:{color:gc(),drawBorder:false}},
                y:{ticks:{color:tc(),font:{size:9},stepSize:1},grid:{color:gc(),drawBorder:false},beginAtZero:true},
            },
        },
    });
}

// ── Confidence ──────────────────────────────
async function loadConf() {
    const data = await get("/api/confidence-trend");
    const labels = data.map(d=>new Date(d.day+"T00:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric"}));

    new Chart(document.getElementById("conf-chart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                { label:"Confidence", data:data.map(d=>(d.confidence*100).toFixed(0)), borderColor:C.blue, backgroundColor:C.blue+"12", fill:true, tension:.4, pointRadius:3, pointBackgroundColor:tbg(), pointBorderColor:C.blue, pointBorderWidth:2, borderWidth:2, yAxisID:"y" },
                { label:"Volume", data:data.map(d=>d.volume), borderColor:C.amber, backgroundColor:"transparent", borderWidth:1.5, borderDash:[4,3], tension:.4, pointRadius:2, pointBackgroundColor:C.amber, pointBorderWidth:0, yAxisID:"y1" },
            ],
        },
        options: {
            responsive:true, maintainAspectRatio:false, interaction:{mode:"index",intersect:false},
            plugins: {
                legend:{position:"top",align:"end",labels:{color:tc(),font:{size:9,family:"'Inter'"},boxWidth:10,boxHeight:2,padding:8}},
                tooltip:{backgroundColor:tbg(),titleColor:ttx(),bodyColor:ttx(),borderColor:tbd(),borderWidth:1,padding:6},
            },
            scales: {
                x:{ticks:{color:tc(),font:{size:9}},grid:{color:gc(),drawBorder:false}},
                y:{position:"left",ticks:{color:C.blue,font:{size:9},callback:v=>v+"%"},grid:{color:gc(),drawBorder:false},min:0,max:100},
                y1:{position:"right",ticks:{color:C.amber,font:{size:9},stepSize:1},grid:{display:false},beginAtZero:true},
            },
        },
    });
}

// ── Topic Breakdown ─────────────────────────
async function loadTopicChart() {
    const data = await get("/api/topic-sentiment");
    const topics = Object.keys(data).slice(0,8);
    const mk = (k,c) => ({ label:k, data:topics.map(t=>data[t]?.[k]||0), backgroundColor:c+"cc", borderWidth:0, borderRadius:2, barThickness:12 });

    new Chart(document.getElementById("topic-chart"), {
        type: "bar",
        data: { labels:topics.map(t=>t.length>14?t.slice(0,14)+"..":t), datasets:[mk("positive",C.green),mk("negative",C.red),mk("neutral",C.gray),mk("mixed",C.amber)] },
        options: {
            responsive:true, maintainAspectRatio:false, indexAxis:"y",
            plugins:{legend:{display:false}},
            scales: {
                x:{stacked:true,ticks:{color:tc(),font:{size:8},stepSize:1},grid:{color:gc()},beginAtZero:true},
                y:{stacked:true,ticks:{color:tc(),font:{size:9}},grid:{display:false}},
            },
        },
    });
}

// ── Sentiment by Source ─────────────────────
async function loadSourceSent() {
    const posts = await get("/api/posts");
    const bySource = {};
    posts.forEach(p => {
        if (!bySource[p.source]) bySource[p.source] = { positive:0, negative:0, neutral:0, mixed:0 };
        bySource[p.source][p.sentiment]++;
    });
    const sources = Object.keys(bySource);
    const mk = (k,c) => ({ label:k, data:sources.map(s=>bySource[s][k]||0), backgroundColor:c+"cc", borderWidth:0, borderRadius:2 });

    new Chart(document.getElementById("source-sent-chart"), {
        type: "bar",
        data: { labels:sources.map(s=>s.toUpperCase()), datasets:[mk("positive",C.green),mk("negative",C.red),mk("neutral",C.gray),mk("mixed",C.amber)] },
        options: {
            responsive:true, maintainAspectRatio:false,
            plugins:{legend:{display:false}},
            scales: {
                x:{stacked:true,ticks:{color:tc(),font:{size:9}},grid:{display:false}},
                y:{stacked:true,ticks:{color:tc(),font:{size:9},stepSize:1},grid:{color:gc()},beginAtZero:true},
            },
        },
    });
}

// ── Topics ──────────────────────────────────
async function loadTopics() {
    const data = await get("/api/topics");
    const el = document.getElementById("topics-grid");
    const mx = data[0]?.count || 1;
    document.getElementById("t-count").textContent = data.length+" topics";
    el.innerHTML = data.map(t=>`<div class="topic-row"><span class="topic-name">${t.name}</span><div class="topic-bar-wrap"><div class="topic-bar"><div class="topic-bar-fill" style="width:${(t.count/mx)*100}%"></div></div><span class="topic-count">${t.count}</span></div></div>`).join("");
}

// ── Feed ────────────────────────────────────
async function loadPosts() {
    const data = await get("/api/posts");
    const el = document.getElementById("feed");
    document.getElementById("f-count").textContent = data.length+" posts";

    el.innerHTML = data.map(p => {
        const time = new Date(p.created_at).toLocaleString("en-US",{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit",hour12:false});
        const sub = p.subreddit ? ` r/${p.subreddit}` : "";
        const topics = p.topics.map(t=>`<span>${t}</span>`).join(" \u00b7 ");
        let thumb = '<span class="fi">&#9632;</span>';
        if (p.url?.startsWith("http")) { try { thumb = `<img src="https://www.google.com/s2/favicons?domain=${new URL(p.url).hostname}&sz=64" onerror="this.parentElement.innerHTML='<span class=fi>&#9632;</span>'" alt="">`; } catch(e){} }

        return `<div class="post-card"><div class="post-thumb">${thumb}</div><div class="post-content"><div class="post-meta"><span class="post-time">${time}</span><span class="src ${p.source}">${p.source.toUpperCase()}${sub}</span><span class="sent ${p.sentiment}">${p.sentiment.toUpperCase()}</span><span class="post-pts">${p.score}pts \u00b7 ${p.num_comments}cmt</span></div><div class="post-title"><a href="${p.url}" target="_blank">${p.title}</a></div><div class="post-sum">${p.summary||""}</div><div class="post-tags">${topics}</div></div></div>`;
    }).join("");
}

// ── Init ────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadOverview();
    loadTrend();
    loadConf();
    loadTopicChart();
    loadSourceSent();
    loadTopics();
    loadPosts();
});
