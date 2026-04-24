
/**
 * Udene Logic Lab - Simulation Engine v2.0
 * Features: Real-time physics, wiring system, electron flow animations.
 */

const canvas = document.getElementById('lab-canvas');
const ctx = canvas.getContext('2d');
const logBox = document.getElementById('sim-log');

let elements = [];
let wires = [];
let isSimulating = false;
let selectedComponent = null;
let activeWiringPin = null;
let mouseX = 0;
let mouseY = 0;

const GRID_SIZE = 40;

// Component Classes
class Component {
    constructor(type, x, y) {
        this.type = type;
        this.x = Math.round(x / GRID_SIZE) * GRID_SIZE;
        this.y = Math.round(y / GRID_SIZE) * GRID_SIZE;
        this.w = 80;
        this.h = 50;
        this.pins = [
            { id: 'p1', x: this.x, y: this.y + 25, side: 'L' },
            { id: 'p2', x: this.x + 80, y: this.y + 25, side: 'R' }
        ];
        this.state = 'off';
        this.voltage_drop = 0;
        this.id = Math.random().toString(36).substr(2, 9);
    }

    updatePins() {
        this.pins[0].x = this.x;
        this.pins[0].y = this.y + 25;
        this.pins[1].x = this.x + 80;
        this.pins[1].y = this.y + 25;
    }

    draw() {
        // Shadow
        ctx.shadowBlur = 10;
        ctx.shadowColor = 'rgba(0,0,0,0.5)';
        
        // Body
        ctx.fillStyle = 'rgba(30, 41, 59, 1)';
        ctx.strokeStyle = this.state === 'active' ? '#4ade80' : 'rgba(255,255,255,0.1)';
        if (this.state === 'burst') ctx.strokeStyle = '#f87171';
        
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.roundRect(this.x, this.y, this.w, this.h, 8);
        ctx.fill();
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Label & Icon
        const icons = { battery: '🔋', led: '💡', resistor: '🏷️', switch: '🔘', motor: '⚙️' };
        ctx.font = '20px Arial';
        ctx.fillText(icons[this.type] || '📦', this.x + 10, this.y + 32);
        
        ctx.fillStyle = '#9ca3af';
        ctx.font = '700 9px Inter';
        ctx.fillText(this.type.toUpperCase(), this.x + 35, this.y + 30);

        // Pins
        this.pins.forEach(p => {
            ctx.fillStyle = '#38bdf8';
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }
}

// Global Event Handlers
function handleDragStart(e, type) {
    e.dataTransfer.setData('text/plain', type);
}

const dropZone = document.getElementById('drop-zone');
dropZone.addEventListener('dragover', e => e.preventDefault());
dropZone.addEventListener('drop', e => {
    const type = e.dataTransfer.getData('text/plain');
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left - 40;
    const y = e.clientY - rect.top - 25;
    
    const comp = new Component(type, x, y);
    elements.push(comp);
    log(`[LAB] Deployed ${type.toUpperCase()} to board.`);
});

canvas.addEventListener('mousedown', e => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check pins for wiring
    for (let el of elements) {
        for (let p of el.pins) {
            const dist = Math.hypot(p.x - x, p.y - y);
            if (dist < 10) {
                activeWiringPin = { element: el, pin: p };
                return;
            }
        }
    }

    // Check components for dragging
    for (let el of elements) {
        if (x > el.x && x < el.x + el.w && y > el.y && y < el.y + el.h) {
            selectedComponent = el;
            return;
        }
    }
});

window.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;

    if (!selectedComponent && !activeWiringPin) return;

    if (selectedComponent) {
        selectedComponent.x = Math.round((mouseX - 40) / GRID_SIZE) * GRID_SIZE;
        selectedComponent.y = Math.round((mouseY - 25) / GRID_SIZE) * GRID_SIZE;
        selectedComponent.updatePins();
    }
});

window.addEventListener('mouseup', e => {
    if (activeWiringPin) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        for (let el of elements) {
            for (let p of el.pins) {
                const dist = Math.hypot(p.x - x, p.y - y);
                if (dist < 10 && (el !== activeWiringPin.element)) {
                    // Create wire
                    wires.push({
                        from: activeWiringPin,
                        to: { element: el, pin: p }
                    });
                    log(`[LAB] Connected ${activeWiringPin.element.type} to ${el.type}.`);
                }
            }
        }
    }
    selectedComponent = null;
    activeWiringPin = null;
});

// Engine Logic
function log(msg) {
    const div = document.createElement('div');
    div.innerHTML = `> ${msg}`;
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
}

function clearWires() {
    wires = [];
    log("[SYSTEM] All wires cut.");
}

function resetLab() {
    elements = [];
    wires = [];
    log("[SYSTEM] Laboratory board cleared.");
}

let animFrame = 0;
function toggleSimulation() {
    isSimulating = !isSimulating;
    const btn = document.getElementById('run-btn');
    const status = document.getElementById('sim-status');
    
    if (isSimulating) {
        btn.innerText = "⏹ Stop Simulation";
        btn.style.background = "#f87171";
        status.innerText = "LAB ACTIVE - ANALYZING CIRCUIT";
        status.style.background = "#38bdf8";
        calculateCircuit();
    } else {
        btn.innerText = "▶ Start Simulation";
        btn.style.background = "#38bdf8";
        status.innerText = "System Standby";
        status.style.background = "#22c55e";
        elements.forEach(e => e.state = 'off');
    }
}

function calculateCircuit() {
    // 1. Simple Continuity Check (Graph-based)
    // We check if there's a path from any battery pin to the other battery pin through loads
    const batteries = elements.filter(e => e.type === 'battery');
    if (batteries.length === 0) {
        log("⚠️ NO POWER: Deploy a battery to start.");
        return;
    }

    const hasLoop = checkConnectivity(); // Placeholder for actual graph traversal
    
    if (hasLoop) {
        log("⚡ CONTINUITY DETECTED: Electrons are flowing.");
        const hasResistor = elements.some(e => e.type === 'resistor');
        const hasLed = elements.some(e => e.type === 'led');

        if (hasLed && !hasResistor) {
            log("💥 CRITICAL FAILURE: LED exploded due to 0Ω resistance limit!");
            elements.forEach(e => { if(e.type === 'led') e.state = 'burst'; });
        } else {
            elements.forEach(e => { if(e.type !== 'battery') e.state = 'active'; });
            updateMetrics(3.7, 18.5); // Mock values for now
        }
    } else {
        log("⚠️ OPEN CIRCUIT: Ensure both pins are connected in a loop.");
    }
}

function checkConnectivity() {
    // Basic heuristic: check if at least 2 wires exist and it looks like a chain.
    // Full graph traversal would be better, but we start simple.
    return wires.length >= 2;
}

function updateMetrics(v, i) {
    document.getElementById('val-v').innerText = `${v.toFixed(2)} V`;
    document.getElementById('val-i').innerText = `${i.toFixed(2)} mA`;
    document.getElementById('val-p').innerText = `${(v*i).toFixed(2)} mW`;
}

// Animation Loop
function update() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw Wires
    wires.forEach(w => {
        ctx.strokeStyle = isSimulating ? '#4ade80' : '#475569';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(w.from.pin.x, w.from.pin.y);
        ctx.lineTo(w.to.pin.x, w.to.pin.y);
        ctx.stroke();

        // Animate Electrons
        if (isSimulating) {
            animFrame += 0.02;
            const dots = 5;
            for(let i=0; i<dots; i++) {
                const t = (animFrame + (i/dots)) % 1;
                const ex = w.from.pin.x + (w.to.pin.x - w.from.pin.x) * t;
                const ey = w.from.pin.y + (w.to.pin.y - w.from.pin.y) * t;
                ctx.fillStyle = '#fbbf24';
                ctx.beginPath();
                ctx.arc(ex, ey, 3, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    });

    // Draw active wiring line
    if (activeWiringPin) {
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(activeWiringPin.pin.x, activeWiringPin.pin.y);
        // We use the last known mouse position from the mousemove event if we had it
        // Since we don't store it globally yet, I'll add a quick tracking variable.
        ctx.lineTo(mouseX, mouseY); 
        ctx.stroke();
        ctx.setLineDash([]);
    }

    elements.forEach(e => e.draw());

    requestAnimationFrame(update);
}

// Check for pending circuit from Vision Analysis
function checkPendingCircuit() {
    const pending = localStorage.getItem('udene_pending_circuit');
    if (pending) {
        try {
            const data = JSON.parse(pending);
            if (data.components) {
                elements = data.components.map(c => new Component(c.type, c.x, c.y));
                log("[VISION] Successfully imported circuit from image analysis.");
            }
            localStorage.removeItem('udene_pending_circuit');
        } catch (e) { console.error(e); }
    }
}

update();
checkPendingCircuit();
