/* ============================================================
   Exercise data — mirrors backend/exercise_rules.py EXERCISE_CONFIG.
   Kept as a static mirror since this frontend is not wired to the
   Python backend; update both if you add/change an exercise.
   ============================================================ */
const EXERCISES = [
  { name: "Squat",            pattern: "flexion",   joint: "knee",    low: 90,  high: 160, tol: 10 },
  { name: "Push-Up",          pattern: "flexion",   joint: "elbow",   low: 90,  high: 160, tol: 0  },
  { name: "Deadlift",         pattern: "extension", joint: "hip",     low: 100, high: 170 },
  { name: "Lunge",            pattern: "flexion",   joint: "knee",    low: 90,  high: 160, tol: 15 },
  { name: "Bicep Curl",       pattern: "flexion",   joint: "elbow",   low: 45,  high: 150, tol: 10 },
  { name: "Shoulder Press",   pattern: "extension", joint: "elbow",   low: 90,  high: 160 },
  { name: "Sit-Up / Crunch",  pattern: "flexion",   joint: "hip",     low: 90,  high: 140, tol: 15 },
  { name: "Jumping Jack",     pattern: "extension", joint: "shoulder",low: 30,  high: 150 },
  { name: "High Knees",       pattern: "flexion",   joint: "hip",     low: 100, high: 160, tol: 15 },
  { name: "Lateral Raise",    pattern: "extension", joint: "shoulder",low: 20,  high: 85  },
  { name: "Tricep Dip",       pattern: "flexion",   joint: "elbow",   low: 90,  high: 160, tol: 10 },
  { name: "Glute Bridge",     pattern: "extension", joint: "hip",     low: 110, high: 170 },
  { name: "Mountain Climber", pattern: "flexion",   joint: "hip",     low: 90,  high: 160, tol: 15 },
  { name: "Calf Raise",       pattern: "extension", joint: "ankle",   low: 70,  high: 110 },
  { name: "Pull-Up",          pattern: "flexion",   joint: "elbow",   low: 70,  high: 160, tol: 15 },
  { name: "Bicycle Crunch",   pattern: "flexion",   joint: "hip",     low: 90,  high: 150, tol: 15 },
];

function renderExerciseGrid() {
  const grid = document.getElementById("exerciseGrid");
  if (!grid) return;

  grid.innerHTML = EXERCISES.map(ex => {
    const badgeClass = ex.pattern === "flexion" ? "badge--flexion" : "badge--extension";
    const tolStr = ex.tol ? ` ±${ex.tol}°` : "";
    return `
      <article class="ex-card">
        <h3 class="ex-card__name">${ex.name}</h3>
        <div class="ex-card__meta">
          <span class="badge ${badgeClass}">${ex.pattern}</span>
          <span>${ex.joint} angle</span>
        </div>
        <div class="ex-card__range">${ex.low}°${tolStr} – ${ex.high}°</div>
      </article>
    `;
  }).join("");
}

/* ============================================================
   Hero rig: a hip-knee-ankle leg whose knee angle is computed with
   the same vector math as pose_utils.calculate_angle() in the
   backend --  θ = |atan2(Δy_a, Δx_a) − atan2(Δy_c, Δx_c)| -- driven
   by an eased squat-depth cycle rather than live camera input.
   ============================================================ */
function initRig() {
  const thighEl = document.getElementById("thigh");
  const shinEl = document.getElementById("shin");
  const arcEl = document.getElementById("arc");
  const hipDot = document.getElementById("hip");
  const kneeDot = document.getElementById("knee");
  const ankleDot = document.getElementById("ankle");
  const angleLabel = document.getElementById("angleValue");
  const stateLabel = document.getElementById("stateValue");

  if (!thighEl) return;

  const HIP = { x: 100, y: 55 };
  const THIGH_LEN = 78;
  const SHIN_LEN = 68;
  const DOWN_THRESHOLD = 100; // matches squat's low_threshold + tolerance

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function angleBetween(a, b, c) {
    // Same formula as the Python backend's calculate_angle()
    const rad = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let deg = Math.abs(rad * 180 / Math.PI);
    if (deg > 180) deg = 360 - deg;
    return deg;
  }

  function draw(depth) {
    // depth: 0 (standing) -> 1 (full squat)
    const thighAngle = depth * 0.85;               // radians from vertical
    const shinAngle = depth * 1.9;                  // shin swings back further

    const knee = {
      x: HIP.x + THIGH_LEN * Math.sin(thighAngle),
      y: HIP.y + THIGH_LEN * Math.cos(thighAngle),
    };
    const ankle = {
      x: knee.x - SHIN_LEN * Math.sin(shinAngle),
      y: knee.y + SHIN_LEN * Math.cos(shinAngle),
    };

    thighEl.setAttribute("x1", HIP.x); thighEl.setAttribute("y1", HIP.y);
    thighEl.setAttribute("x2", knee.x); thighEl.setAttribute("y2", knee.y);
    shinEl.setAttribute("x1", knee.x); shinEl.setAttribute("y1", knee.y);
    shinEl.setAttribute("x2", ankle.x); shinEl.setAttribute("y2", ankle.y);

    hipDot.setAttribute("cx", HIP.x); hipDot.setAttribute("cy", HIP.y);
    kneeDot.setAttribute("cx", knee.x); kneeDot.setAttribute("cy", knee.y);
    ankleDot.setAttribute("cx", ankle.x); ankleDot.setAttribute("cy", ankle.y);

    const angle = angleBetween(HIP, knee, ankle);

    // small arc sweep at the knee, purely decorative but sized to the angle
    const r = 18;
    const startX = knee.x + r * Math.cos(0);
    const startY = knee.y - r * Math.sin(0);
    const sweep = (180 - angle) * (Math.PI / 180);
    const endX = knee.x + r * Math.cos(sweep);
    const endY = knee.y - r * Math.sin(sweep);
    arcEl.setAttribute("d", `M ${startX} ${startY} A ${r} ${r} 0 0 0 ${endX} ${endY}`);

    angleLabel.textContent = `${Math.round(angle)}°`;

    const isDown = angle <= DOWN_THRESHOLD;
    stateLabel.textContent = isDown ? "DOWN" : "UP";
    stateLabel.classList.toggle("is-down", isDown);
  }

  if (prefersReducedMotion) {
    draw(0.5);
    return;
  }

  const CYCLE_MS = 2600;
  function tick(t) {
    const phase = (t % CYCLE_MS) / CYCLE_MS;             // 0..1
    const depth = (1 - Math.cos(phase * Math.PI * 2)) / 2; // eased 0..1..0
    draw(depth);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

document.addEventListener("DOMContentLoaded", () => {
  renderExerciseGrid();
  initRig();
});
