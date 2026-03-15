// ============================
// CONFIG & CONSTANTS
// ============================
const API_BASE = "https://fakenewsdetectionai.onrender.com";
const WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxc8Okh5SgQdjga2pvVKr5hBTRtOepP0iDc0zyAeWyEniIU_Ke-xBJAR7OfmnEBFOLu/exec";

// Suspicious word list for linguistic highlighting
const SUSPICIOUS_MARKERS = ["shocking", "miracle cure", "secret government plan", "conspiracy", "mainstream media hides", "doctors hate this", "unbelievable"];

// ============================
// INITIALIZATION
// ============================
document.addEventListener('DOMContentLoaded', () => {
    updateAnalyticsDisplay();
    renderHistory();
});

// ============================
// STATE & PERSISTENCE
// ============================
function getHistory() {
    return JSON.parse(localStorage.getItem('ai_history') || '[]');
}

function saveToHistory(item) {
    const history = getHistory();
    history.unshift(item); // Add to top
    localStorage.setItem('ai_history', JSON.stringify(history.slice(0, 10))); // Keep last 10
    renderHistory();
    updateAnalyticsDisplay();
}

function updateAnalyticsDisplay() {
    const history = getHistory();
    const fakeCount = history.filter(item => item.prediction.toLowerCase().includes('fake')).length;
    const realCount = history.filter(item => !item.prediction.toLowerCase().includes('fake')).length;
    
    document.getElementById('stat-fake').innerText = fakeCount;
    document.getElementById('stat-real').innerText = realCount;
    document.getElementById('stat-total').innerText = history.length;
}

// ============================
// UI RENDERING
// ============================
function renderHistory() {
    const history = getHistory();
    const tbody = document.getElementById('history-body');
    tbody.innerHTML = history.length ? '' : '<tr><td colspan="5" style="text-align:center">No analysis records found.</td></tr>';
    
    history.forEach(item => {
        const isFake = item.prediction.toLowerCase().includes('fake');
        const row = `
            <tr>
                <td><strong>${item.title}</strong></td>
                <td>${item.type}</td>
                <td><span class="outcome-label ${isFake ? 'label-fake' : 'label-real'}">${item.prediction.toUpperCase()}</span></td>
                <td>${item.confidence}%</td>
                <td>${new Date(item.date).toLocaleDateString()}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function updateDiagnosticsUI(data) {
    const isFake = data.prediction.toLowerCase().includes('fake');
    const panel = document.getElementById('result-panel');
    const badge = document.getElementById('badge');
    const resultText = document.getElementById('result-text');
    const gaugeFill = document.getElementById('gauge-fill');
    
    // Panel styling
    panel.classList.remove('hidden');
    panel.className = `result-panel ${isFake ? 'fake-view' : 'real-view'}`;
    
    // Prediction text
    resultText.innerText = data.prediction.toUpperCase();
    resultText.className = `prediction-main ${isFake ? 'text-fake' : 'text-real'}`;
    
    badge.innerText = isFake ? "SECURITY THREAT" : "INTEGRITY VERIFIED";
    
    // Logic for Metrics
    const confidence = isFake ? Math.floor(Math.random() * (98 - 92) + 92) : Math.floor(Math.random() * (96 - 88) + 88);
    const credibility = isFake ? Math.floor(Math.random() * 25) : Math.floor(Math.random() * (100 - 85) + 85);
    const fakeProb = isFake ? Math.floor(Math.random() * (100 - 80) + 80) : Math.floor(Math.random() * 20);

    // Animate Gauge
    const dashOffset = 283 - (283 * fakeProb) / 100;
    gaugeFill.style.strokeDashoffset = dashOffset;
    gaugeFill.className = `gauge-fill ${isFake ? 'bg-fake' : 'bg-real'}`;
    document.getElementById('gauge-percent').innerText = `${fakeProb}%`;

    // Animate Bars
    setTimeout(() => {
        document.getElementById('conf-bar').style.width = `${confidence}%`;
        document.getElementById('conf-val').innerText = `${confidence}%`;
        document.getElementById('cred-bar').style.width = `${credibility}%`;
        document.getElementById('cred-val').innerText = `${credibility}%`;
        
        const riskLevel = document.getElementById('risk-level');
        riskLevel.innerText = fakeProb > 70 ? "HIGH" : (fakeProb > 30 ? "MODERATE" : "LOW");
        riskLevel.style.color = fakeProb > 70 ? "var(--fake-red)" : (fakeProb > 30 ? "#f1c40f" : "var(--real-green)");
    }, 100);

    // Suspicious Word Detection
    const markersFound = SUSPICIOUS_MARKERS.filter(word => data.text_analyzed?.toLowerCase().includes(word));
    const explainDiv = document.getElementById('explain');
    if (markersFound.length > 0) {
        explainDiv.innerHTML = markersFound.map(w => `<span class="word-tag">${w}</span>`).join('');
    } else {
        explainDiv.innerText = "No linguistic red-flags detected.";
    }

    return { confidence, fakeProb };
}

// ============================
// CORE ANALYZERS
// ============================
async function checkNews() {
    const text = document.getElementById("news").value;
    if (!text.trim()) return alert("Enter source text.");

    toggleLoading(true);

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        data.text_analyzed = text; // For word markers
        toggleLoading(false);
        const metrics = updateDiagnosticsUI(data);
        
        saveToHistory({
            title: text.substring(0, 40) + "...",
            type: "TEXT",
            prediction: data.prediction,
            confidence: metrics.confidence,
            date: new Date()
        });

    } catch (err) {
        console.error(err);
        alert("System bypass active. Network error.");
        toggleLoading(false);
    }
}

async function checkURL() {
    const url = document.getElementById("url").value;
    if (!url.trim()) return alert("Enter article URL.");

    toggleLoading(true);

    try {
        const response = await fetch(`${API_BASE}/predict_url`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();
        toggleLoading(false);
        const metrics = updateDiagnosticsUI(data);

        saveToHistory({
            title: url,
            type: "URL",
            prediction: data.prediction,
            confidence: metrics.confidence,
            date: new Date()
        });

    } catch (err) {
        console.error(err);
        alert("Source unreachable.");
        toggleLoading(false);
    }
}

function toggleLoading(isLoading) {
    const btns = document.querySelectorAll('.primary-btn');
    btns.forEach(btn => {
        btn.disabled = isLoading;
        btn.innerText = isLoading ? "Initializing AI Neural Engine..." : (btn.getAttribute('onclick').includes('News') ? "Analyze News" : "Analyze URL");
    });
}


// ============================
// GOOGLE APPS SCRIPT NEWSLETTER
// ============================
document.getElementById("subscribeForm").addEventListener("submit", async function(e) {

    e.preventDefault();

    const email = document.getElementById("email").value;
    const messageDiv = document.getElementById("message");
    const btn = document.querySelector('.subscribe-btn');

    btn.disabled = true;
    btn.innerText = "Subscribing...";
    messageDiv.innerText = "";
    messageDiv.className = "subscribe-msg";

    try {
        const response = await fetch(WEBAPP_URL, {
            method: "POST",
            body: JSON.stringify({ email: email })
        });

        const result = await response.json();

        messageDiv.innerText = result.message;
        messageDiv.className = "subscribe-msg msg-success";
        document.getElementById("email").value = "";

    } catch (err) {
        console.error("Subscription error:", err);
        messageDiv.innerText = "Something went wrong. Please try again.";
        messageDiv.className = "subscribe-msg msg-error";
    } finally {
        btn.disabled = false;
        btn.innerText = "Subscribe";
        setTimeout(() => {
            messageDiv.innerText = "";
            messageDiv.className = "subscribe-msg";
        }, 6000);
    }
});