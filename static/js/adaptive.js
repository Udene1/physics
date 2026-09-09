async function adaptiveJson(url, options = {}) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Adaptive request failed');
    return data;
}

function adaptiveEscape(value) {
    return String(value ?? '').replace(/[&<>\"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;' }[char]));
}

async function loadAdaptive() {
    const container = document.getElementById('adaptive-content');
    if (!container) return;
    container.innerHTML = '<p>Reading your durable learning state...</p>';
    try {
        const data = await adaptiveJson('/adaptive/snapshot');
        const journey = data.journey || {};
        const selected = data.selectedIntervention;
        const message = data.interventionMessage;
        const misconceptions = data.activeMisconceptions || [];
        const reviews = data.dueReviews || [];
        let html = `<div style="display:grid;gap:1rem;max-width:900px">`;
        html += `<div class="message assistant-message"><div class="message-label">🧠 VITA</div><div class="message-content"><strong>You are here:</strong> ${adaptiveEscape(journey.location || data.currentConcept || 'learning')}<br><strong>Next:</strong> ${adaptiveEscape(data.nextConcept || 'No new concept yet')}</div></div>`;
        if (message) html += `<div class="message assistant-message"><div class="message-label">🎯 TARGETED REPAIR</div><div class="message-content"><strong>Blocking you:</strong> ${adaptiveEscape(message.blocking)}<br><strong>Vita noticed:</strong> ${adaptiveEscape(message.noticed)}<br><strong>Why repair this:</strong> ${adaptiveEscape(message.why)}</div></div>`;
        if (selected) {
            html += `<div class="message assistant-message"><div class="message-label">🧪 ${adaptiveEscape(selected.stage).toUpperCase()}</div><div class="message-content"><h3>${adaptiveEscape(selected.problemId)}</h3><p>${adaptiveEscape(data.intervention?.strategy || selected.strategy)}</p><button class="btn btn-primary" onclick="loadAdaptiveProblem(${selected.id})">Open targeted problem</button></div></div>`;
        }
        if (misconceptions.length) html += `<div class="message assistant-message"><div class="message-label">🔎 ACTIVE EVIDENCE</div><div class="message-content">${misconceptions.map(m => `<div><strong>${adaptiveEscape(m.code)}</strong> · severity ${m.severity} · ${m.occurrences} signal(s)</div>`).join('')}</div></div>`;
        if (data.demonstratedRepair) html += `<div class="message assistant-message"><div class="message-label">✅ DEMONSTRATED REPAIR</div><div class="message-content">${adaptiveEscape(data.demonstratedRepair)}</div></div>`;
        if (reviews.length) html += `<div class="message assistant-message"><div class="message-label">📅 RETRIEVAL REVIEW</div><div class="message-content">${reviews.length} concept review(s) are due. <button class="btn btn-primary" onclick="loadAdaptiveReview()">Open review</button></div></div>`;
        html += `<div id="adaptive-problem"></div></div>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p class="error">Adaptive engine unavailable: ${adaptiveEscape(error.message)}</p>`;
    }
}

async function loadAdaptiveProblem(interventionId) {
    const container = document.getElementById('adaptive-problem');
    if (!container) return;
    try {
        const data = await adaptiveJson('/adaptive/intervention');
        if (!data.intervention || data.intervention.id !== interventionId) throw new Error('Intervention changed; refresh the journey.');
        const p = data.problem;
        container.innerHTML = `<div class="message assistant-message"><div class="message-label">🧩 SOLVE</div><div class="message-content"><h3>${adaptiveEscape(p.prompt)}</h3><p><strong>Givens:</strong> ${p.givens.map(adaptiveEscape).join(' · ')}</p><textarea id="adaptive-reasoning" rows="6" placeholder="Show your reasoning, equations, assumptions and units..." style="width:100%;margin:.5rem 0;padding:.75rem"></textarea><input id="adaptive-answer" placeholder="Final answer" style="width:100%;margin:.5rem 0;padding:.75rem"><button class="btn btn-primary" onclick="submitAdaptiveProblem(${interventionId})">Submit reasoning</button></div></div>`;
    } catch (error) {
        container.innerHTML = `<p class="error">${adaptiveEscape(error.message)}</p>`;
    }
}

async function submitAdaptiveProblem(interventionId) {
    const reasoning = document.getElementById('adaptive-reasoning')?.value.trim();
    const answer = document.getElementById('adaptive-answer')?.value.trim();
    if (!reasoning || !answer) return;
    try {
        const data = await adaptiveJson('/adaptive/remediation', { method: 'POST', body: JSON.stringify({ interventionId, reasoning, answer }) });
        const e = data.evaluation;
        const container = document.getElementById('adaptive-content');
        container.innerHTML = `<div class="message assistant-message"><div class="message-label">${e.verdict === 'repaired' ? '✅ REPAIR EVIDENCE' : '🔎 MORE EVIDENCE NEEDED'}</div><div class="message-content"><strong>Verdict:</strong> ${adaptiveEscape(e.verdict)}<br><strong>Reasoning checkpoints:</strong> ${e.checkpointScore}<br>${(e.missingCheckpoints || []).length ? `<strong>Still missing:</strong> ${e.missingCheckpoints.map(adaptiveEscape).join(', ')}` : 'All diagnostic checkpoints were demonstrated.'}<br><button class="btn btn-primary" onclick="loadAdaptive()">Refresh journey</button></div></div>`;
    } catch (error) {
        const container = document.getElementById('adaptive-content');
        container.insertAdjacentHTML('beforeend', `<p class="error">${adaptiveEscape(error.message)}</p>`);
    }
}

async function loadAdaptiveReview() {
    const container = document.getElementById('adaptive-content');
    try {
        const data = await adaptiveJson('/adaptive/review');
        if (!data.review || !data.problem) { container.insertAdjacentHTML('beforeend', '<p>No review is due right now.</p>'); return; }
        const p = data.problem;
        container.innerHTML = `<div class="message assistant-message"><div class="message-label">📅 RETRIEVAL REVIEW</div><div class="message-content"><h3>${adaptiveEscape(p.prompt)}</h3><textarea id="review-reasoning" rows="6" placeholder="Show your reasoning..."></textarea><input id="review-answer" placeholder="Final answer"><button class="btn btn-primary" onclick="submitAdaptiveReview()">Submit review</button></div></div>`;
    } catch (error) { container.innerHTML = `<p class="error">${adaptiveEscape(error.message)}</p>`; }
}

async function submitAdaptiveReview() {
    const reasoning = document.getElementById('review-reasoning')?.value.trim();
    const answer = document.getElementById('review-answer')?.value.trim();
    if (!reasoning || !answer) return;
    try {
        const data = await adaptiveJson('/adaptive/review', { method: 'POST', body: JSON.stringify({ reasoning, answer }) });
        document.getElementById('adaptive-content').innerHTML = `<div class="message assistant-message"><div class="message-label">${data.outcome === 'retained' ? '✅ RETAINED' : '🔁 REPAIR LOOP'}</div><div class="message-content">Review outcome: <strong>${adaptiveEscape(data.outcome)}</strong><br><button class="btn btn-primary" onclick="loadAdaptive()">Refresh journey</button></div></div>`;
    } catch (error) { document.getElementById('adaptive-content').insertAdjacentHTML('beforeend', `<p class="error">${adaptiveEscape(error.message)}</p>`); }
}
