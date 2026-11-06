// Draws a 2D chemical structure (SVG) from a SMILES string. No libraries: written for DermaLens.
// Supports Kekule SMILES: atoms, branches (), ring digits, = and # bonds, [bracket atoms] with charge and H,
// and "." for salts. Layout idea: rings become regular polygons (fused rings share an edge), and chains
// zig-zag at 120 degrees. It is a clear teaching drawing, not a publication-grade depiction.

const VALENCES = { B: [3], C: [4], N: [3, 5], O: [2], P: [3, 5], S: [2, 4, 6], Si: [4], F: [1], Cl: [1], Br: [1], I: [1] };
const ORGANIC = ["Cl", "Br", "Si", "B", "C", "N", "O", "P", "S", "F", "I"];
const COLORS = { O: "#d9534f", N: "#4a78d4", S: "#b8860b", P: "#d9822b", F: "#2f9e5a", Cl: "#2f9e5a", Br: "#a0522d", I: "#8a4fb0" };
const SVG_NS = "http://www.w3.org/2000/svg";
const L = 36; // bond length in px

export function parseSmiles(smiles) {
  const atoms = [], bonds = [], stack = [], rings = {};
  let prev = null, order = 0, i = 0;
  while (i < smiles.length) {
    const c = smiles[i];
    if (c === "(") { stack.push(prev); i++; continue; }
    if (c === ")") { prev = stack.pop(); i++; continue; }
    if (c === ".") { prev = null; order = 0; i++; continue; }
    if (c === "-" || c === "=" || c === "#") { order = c === "-" ? 1 : c === "=" ? 2 : 3; i++; continue; }
    if (c === "/" || c === "\\") { i++; continue; }
    if (/\d/.test(c) || c === "%") {
      const key = c === "%" ? smiles.substr(i + 1, 2) : c;
      i += c === "%" ? 3 : 1;
      if (key in rings) { const [a, o] = rings[key]; delete rings[key]; bonds.push({ a, b: prev, order: order || o || 1 }); }
      else rings[key] = [prev, order];
      order = 0;
      continue;
    }
    let atom;
    if (c === "[") {
      const j = smiles.indexOf("]", i);
      const m = /^(\d*)([A-Z][a-z]?)@{0,2}(?:(H)(\d*))?(\+\+|--|[+-]\d*)?$/.exec(smiles.slice(i + 1, j));
      if (!m) throw new Error("Bad atom " + smiles.slice(i, j + 1));
      let charge = 0;
      if (m[5]) charge = m[5] === "++" ? 2 : m[5] === "--" ? -2 : (m[5][0] === "+" ? 1 : -1) * Number(m[5].slice(1) || 1);
      atom = { el: m[2], charge, h: m[3] ? Number(m[4] || 1) : 0 };
      i = j + 1;
    } else {
      const el = ORGANIC.find((o) => smiles.startsWith(o, i));
      if (!el) throw new Error("Unexpected character " + c);
      atom = { el, charge: 0, h: null };
      i += el.length;
    }
    atoms.push(atom);
    const idx = atoms.length - 1;
    if (prev !== null) bonds.push({ a: prev, b: idx, order: order || 1 });
    order = 0; prev = idx;
  }
  const used = atoms.map(() => 0);
  bonds.forEach((b) => { used[b.a] += b.order; used[b.b] += b.order; });
  atoms.forEach((at, k) => {
    if (at.h === null) {
      const opts = VALENCES[at.el];
      const val = opts.find((v) => v >= used[k]) ?? opts[opts.length - 1];
      at.h = Math.max(0, val - used[k]);
    }
  });
  return { atoms, bonds };
}

function adjacency(n, bonds) {
  const adj = Array.from({ length: n }, () => []);
  bonds.forEach((b, k) => { adj[b.a].push({ to: b.b, k }); adj[b.b].push({ to: b.a, k }); });
  return adj;
}

// Smallest rings: for every bond, the shortest loop through it; keep rings that cover new bonds.
function findRings(n, bonds, adj) {
  const found = new Map();
  bonds.forEach((bd, k) => {
    const prevOf = new Map([[bd.a, null]]);
    const queue = [bd.a];
    while (queue.length && !prevOf.has(bd.b)) {
      const u = queue.shift();
      for (const { to, k: kk } of adj[u]) {
        if (kk === k || prevOf.has(to)) continue;
        prevOf.set(to, u); queue.push(to);
      }
    }
    if (!prevOf.has(bd.b)) return;
    const path = [];
    for (let v = bd.b; v !== null; v = prevOf.get(v)) path.push(v);
    if (path.length > 12) return;
    const key = [...path].sort((x, y) => x - y).join(",");
    if (!found.has(key)) found.set(key, path);
  });
  const cands = [...found.values()].sort((x, y) => x.length - y.length);
  const covered = new Set(), chosen = [];
  const bondKey = (x, y) => (x < y ? x + "-" + y : y + "-" + x);
  for (const ring of cands) {
    const keys = ring.map((v, j) => bondKey(v, ring[(j + 1) % ring.length]));
    if (keys.some((kk) => !covered.has(kk))) { keys.forEach((kk) => covered.add(kk)); chosen.push(ring); }
  }
  return chosen;
}

const rot = (ang, d) => ang + d;
const unit = (ang) => [Math.cos(ang), Math.sin(ang)];
const angleOf = (from, to) => Math.atan2(to[1] - from[1], to[0] - from[0]);
const norm = (a) => { while (a < 0) a += 2 * Math.PI; while (a >= 2 * Math.PI) a -= 2 * Math.PI; return a; };

function layoutComponent(atomIdx, adj, rings, pos) {
  const inComp = new Set(atomIdx);
  const myRings = rings.filter((r) => inComp.has(r[0]));
  const ringsOf = new Map();
  myRings.forEach((r, ri) => r.forEach((v) => { if (!ringsOf.has(v)) ringsOf.set(v, []); ringsOf.get(v).push(ri); }));
  const placedRing = new Set();
  const turn = new Map();
  const queue = [];

  const subtree = (v, from) => {
    const seen = new Set([from, v]); const todo = [v]; let count = 0;
    while (todo.length) { const u = todo.pop(); count++; for (const { to } of adj[u]) if (!seen.has(to)) { seen.add(to); todo.push(to); } }
    return count;
  };
  const ringCenter = (ring) => {
    const pts = ring.filter((v) => pos.has(v)).map((v) => pos.get(v));
    return [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];
  };
  const radius = (n) => L / (2 * Math.sin(Math.PI / n));

  function placePolygon(ring, center, anchor, anchorAngle, step) {
    const n = ring.length, R = radius(n), i0 = ring.indexOf(anchor);
    for (let j = 0; j < n; j++) {
      const v = ring[(i0 + j) % n];
      if (pos.has(v)) continue;
      const a = anchorAngle + step * j;
      pos.set(v, [center[0] + R * Math.cos(a), center[1] + R * Math.sin(a)]);
      queue.push(v);
    }
  }
  function spreadFused(startRi) {
    let changed = true;
    placedRing.add(startRi);
    while (changed) {
      changed = false;
      myRings.forEach((ring, ri) => {
        if (placedRing.has(ri)) return;
        const n = ring.length;
        // a shared edge: two neighbouring atoms of this ring that are already placed
        let edge = -1;
        for (let j = 0; j < n; j++) if (pos.has(ring[j]) && pos.has(ring[(j + 1) % n])) { edge = j; break; }
        if (edge < 0) return;
        const A = ring[edge], B = ring[(edge + 1) % n];
        const pa = pos.get(A), pb = pos.get(B);
        const mid = [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2];
        // push the new ring away from the rings that are already drawn on this edge
        let ref = null;
        for (const rj of placedRing) if (myRings[rj].includes(A) && myRings[rj].includes(B)) ref = ringCenter(myRings[rj]);
        const apothem = L / (2 * Math.tan(Math.PI / n));
        let nx = -(pb[1] - pa[1]) / L, ny = (pb[0] - pa[0]) / L;
        if (ref && (ref[0] - mid[0]) * nx + (ref[1] - mid[1]) * ny > 0) { nx = -nx; ny = -ny; }
        const center = [mid[0] + nx * apothem, mid[1] + ny * apothem];
        const aA = angleOf(center, pa), aB = angleOf(center, pb);
        let d = norm(aB - aA); const step0 = (2 * Math.PI) / n;
        const step = d < Math.PI ? step0 : -step0;
        // walk the ring starting at A in the direction of B
        const order = ring.slice(edge).concat(ring.slice(0, edge));
        for (let j = 0; j < n; j++) {
          const v = order[j];
          if (pos.has(v)) continue;
          const a = aA + step * j;
          pos.set(v, [center[0] + radius(n) * Math.cos(a), center[1] + radius(n) * Math.sin(a)]);
          queue.push(v);
        }
        placedRing.add(ri); changed = true;
      });
    }
  }

  // ---- start
  let start;
  if (myRings.length) {
    const ri = myRings.reduce((best, r, k) => (r.length > myRings[best].length ? k : best), 0);
    const ring = myRings[ri];
    pos.set(ring[0], [0, 0]);
    placePolygon(ring, [0, radius(ring.length)], ring[0], -Math.PI / 2, (2 * Math.PI) / ring.length);
    queue.push(ring[0]);
    spreadFused(ri);
  } else {
    // begin at one end of the longest chain so it runs left to right
    const far = (s) => { const dist = new Map([[s, 0]]); const q = [s]; let last = s; while (q.length) { const u = q.shift(); last = u; for (const { to } of adj[u]) if (!dist.has(to)) { dist.set(to, dist.get(u) + 1); q.push(to); } } return last; };
    start = far(far(atomIdx[0]));
    pos.set(start, [0, 0]); queue.push(start);
  }

  // ---- expand
  while (queue.length) {
    const u = queue.shift();
    const pu = pos.get(u);
    const placedNb = adj[u].filter(({ to }) => pos.has(to)).map(({ to }) => to);
    const open = adj[u].filter(({ to }) => !pos.has(to)).map(({ to }) => to);
    if (!open.length) continue;
    // order unplaced neighbours: biggest branch first
    open.sort((x, y) => subtree(y, u) - subtree(x, u));
    const angles = placedNb.map((v) => norm(angleOf(pu, pos.get(v)))).sort((x, y) => x - y);
    let targets = [];
    if (!angles.length) {
      const k = open.length;
      targets = open.map((v, j) => [v, -Math.PI / 6 + (j * 2 * Math.PI) / k]);
    } else if (angles.length === 1 && open.length === 1 && !(ringsOf.has(u))) {
      const dIn = norm(angles[0] + Math.PI) ; // direction of travel
      const s = turn.has(u) ? -turn.get(u) : 1;
      targets = [[open[0], dIn + s * (Math.PI / 3)]];
      turn.set(open[0], s);
    } else if (angles.length === 1 && !ringsOf.has(u)) {
      const dIn = norm(angles[0] + Math.PI);
      const s = turn.has(u) ? -turn.get(u) : 1;
      const k = open.length;
      if (k === 2) targets = [[open[0], dIn + s * (Math.PI / 3)], [open[1], dIn - s * (Math.PI / 3)]];
      else targets = open.map((v, j) => [v, dIn + (j - (k - 1) / 2) * (2 * Math.PI) / (k + 1) * -s]);
      turn.set(open[0], s);
    } else {
      // general case: put the new bonds into the widest empty angle
      const gaps = angles.map((a, j) => {
        const next = j + 1 < angles.length ? angles[j + 1] : angles[0] + 2 * Math.PI;
        return { from: a, size: next - a };
      });
      const insideRing = (g) => { // does the middle of this gap point into an already drawn ring?
        const mid = g.from + g.size / 2;
        const px = pu[0] + 0.45 * L * Math.cos(mid), py = pu[1] + 0.45 * L * Math.sin(mid);
        return myRings.some((ring, ri) => placedRing.has(ri) && Math.hypot(px - ringCenter(ring)[0], py - ringCenter(ring)[1]) < (L / (2 * Math.tan(Math.PI / ring.length))) * 0.92);
      };
      const usable = gaps.filter((g) => !insideRing(g));
      const best = (usable.length ? usable : gaps).reduce((b, g) => (g.size > b.size ? g : b));
      const bestGap = best.size, from = best.from;
      const k = open.length;
      targets = open.map((v, j) => [v, from + (bestGap * (j + 1)) / (k + 1)]);
    }
    for (const [v, ang] of targets) {
      if (pos.has(v)) continue;
      const [dx, dy] = unit(ang);
      const ringIdx = (ringsOf.get(v) || []).find((ri) => !placedRing.has(ri));
      if (ringIdx !== undefined && !(ringsOf.get(u) || []).includes(ringIdx)) {
        // v is the way into a ring that is not drawn yet: draw the whole ring, away from u
        pos.set(v, [pu[0] + L * dx, pu[1] + L * dy]);
        const ring = myRings[ringIdx];
        const center = [pu[0] + (L + radius(ring.length)) * dx, pu[1] + (L + radius(ring.length)) * dy];
        placePolygon(ring, center, v, angleOf(center, pos.get(v)), (2 * Math.PI) / ring.length);
        queue.push(v);
        spreadFused(ringIdx);
      } else {
        pos.set(v, [pu[0] + L * dx, pu[1] + L * dy]);
        queue.push(v);
      }
    }
  }
  // anything left over (bridged rings): put it next to a placed neighbour so the drawing never breaks
  atomIdx.forEach((v) => {
    if (pos.has(v)) return;
    const nb = adj[v].find(({ to }) => pos.has(to));
    const base = nb ? pos.get(nb.to) : [0, 0];
    pos.set(v, [base[0] + L * 0.5, base[1] + L * 0.5]);
  });
}

// Nudge crowded side branches: rotate a small branch around the atom it hangs from until atoms stop overlapping.
function relax(comp, adj, rings, pos) {
  const MIN = 0.62 * L;
  const inRing = (a, b) => rings.some((r) => r.includes(a) && r.includes(b));
  const moves = [];
  for (const u of comp) for (const { to: v } of adj[u]) {
    if (inRing(u, v)) continue;
    const seen = new Set([u, v]), todo = [v];
    while (todo.length) { const x = todo.pop(); for (const { to } of adj[x]) if (!seen.has(to)) { seen.add(to); todo.push(to); } }
    seen.delete(u);
    if (seen.size <= 30) moves.push({ u, branch: [...seen] });
  }
  const clashCount = () => {
    let c = 0;
    for (let i = 0; i < comp.length; i++) for (let j = i + 1; j < comp.length; j++) {
      const a = pos.get(comp[i]), b = pos.get(comp[j]);
      if (Math.hypot(a[0] - b[0], a[1] - b[1]) < MIN && !adj[comp[i]].some((n) => n.to === comp[j])) c++;
    }
    return c;
  };
  let current = clashCount();
  for (let iter = 0; iter < 25 && current > 0; iter++) {
    let best = null;
    for (const mv of moves) {
      const pu = pos.get(mv.u), saved = mv.branch.map((v) => pos.get(v));
      for (let deg = -150; deg <= 150; deg += 30) {
        if (!deg) continue;
        const t = (deg * Math.PI) / 180, cs = Math.cos(t), sn = Math.sin(t);
        mv.branch.forEach((v, k) => { const [x, y] = saved[k]; pos.set(v, [pu[0] + (x - pu[0]) * cs - (y - pu[1]) * sn, pu[1] + (x - pu[0]) * sn + (y - pu[1]) * cs]); });
        const c = clashCount();
        if (c < current && (!best || c < best.c || (c === best.c && mv.branch.length < best.mv.branch.length))) best = { c, mv, deg };
      }
      mv.branch.forEach((v, k) => pos.set(v, saved[k]));
    }
    if (!best) break;
    const pu = pos.get(best.mv.u), t = (best.deg * Math.PI) / 180, cs = Math.cos(t), sn = Math.sin(t);
    best.mv.branch.forEach((v) => { const [x, y] = pos.get(v); pos.set(v, [pu[0] + (x - pu[0]) * cs - (y - pu[1]) * sn, pu[1] + (x - pu[0]) * sn + (y - pu[1]) * cs]); });
    current = best.c;
  }
}

export function buildLayout(smiles) {
  const mol = parseSmiles(smiles);
  const n = mol.atoms.length;
  const adj = adjacency(n, mol.bonds);
  const rings = findRings(n, mol.bonds, adj);
  const seen = new Set(), comps = [];
  for (let s = 0; s < n; s++) {
    if (seen.has(s)) continue;
    const comp = [], todo = [s];
    while (todo.length) { const u = todo.pop(); if (seen.has(u)) continue; seen.add(u); comp.push(u); adj[u].forEach(({ to }) => todo.push(to)); }
    comps.push(comp.sort((x, y) => x - y));
  }
  const pos = new Map();
  let cursorX = 0;
  comps.forEach((comp) => {
    const local = new Map();
    layoutComponent(comp, adj, rings, local);
    relax(comp, adj, rings, local);
    const xs = comp.map((v) => local.get(v)[0]), ys = comp.map((v) => local.get(v)[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs), midY = (Math.min(...ys) + Math.max(...ys)) / 2;
    comp.forEach((v) => { const [x, y] = local.get(v); pos.set(v, [x - minX + cursorX, y - midY]); });
    cursorX += maxX - minX + L * 1.3;
  });
  return { ...mol, adj, rings, pos };
}

function el(tag, attrs = {}, text) {
  const e = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text !== undefined) e.textContent = text;
  return e;
}

const SUB = "₀₁₂₃₄₅₆₇₈₉";
const sub = (n) => String(n).split("").map((d) => SUB[d]).join("");
const SUPER_PLUS = "⁺", SUPER_MINUS = "⁻";

export function drawStructure(smiles, label) {
  const m = buildLayout(smiles);
  const { atoms, bonds, adj, rings, pos } = m;
  const FS = 15;
  const labelled = atoms.map((a, k) => a.el !== "C" || adj[k].length === 0 || a.charge !== 0);
  const pts = [...pos.values()];
  const pad = 0.9 * L;
  const minX = Math.min(...pts.map((p) => p[0])) - pad, maxX = Math.max(...pts.map((p) => p[0])) + pad;
  const minY = Math.min(...pts.map((p) => p[1])) - pad, maxY = Math.max(...pts.map((p) => p[1])) + pad;
  const W = maxX - minX, H = maxY - minY;
  const svg = el("svg", { viewBox: `${minX} ${minY} ${W} ${H}`, width: Math.round(Math.max(220, Math.min(820, W))), role: "img", "aria-label": label || "Chemical structure", class: "structure-svg" });
  svg.append(el("title", {}, label || "Chemical structure"));
  const g = el("g", { stroke: "currentColor", "stroke-width": "1.8", "stroke-linecap": "round", fill: "none" });
  svg.append(g);

  const trim = (k, from, to) => { // shorten a line where it meets an atom label
    const [x1, y1] = pos.get(from), [x2, y2] = pos.get(to);
    const d = Math.hypot(x2 - x1, y2 - y1) || 1;
    const t1 = labelled[from] ? 0.55 * FS : 0, t2 = labelled[to] ? 0.55 * FS : 0;
    return [x1 + ((x2 - x1) / d) * t1, y1 + ((y2 - y1) / d) * t1, x2 - ((x2 - x1) / d) * t2, y2 - ((y2 - y1) / d) * t2];
  };
  const line = (x1, y1, x2, y2) => g.append(el("line", { x1, y1, x2, y2 }));
  bonds.forEach((b, k) => {
    const [x1, y1, x2, y2] = trim(k, b.a, b.b);
    const d = Math.hypot(x2 - x1, y2 - y1) || 1;
    const nx = -(y2 - y1) / d, ny = (x2 - x1) / d; // unit normal
    if (b.order === 1) return line(x1, y1, x2, y2);
    if (b.order === 3) {
      const o = 0.12 * L;
      line(x1, y1, x2, y2); line(x1 + nx * o, y1 + ny * o, x2 + nx * o, y2 + ny * o); line(x1 - nx * o, y1 - ny * o, x2 - nx * o, y2 - ny * o);
      return;
    }
    const ring = rings.find((r) => r.includes(b.a) && r.includes(b.b));
    if (ring) { // inner parallel line, towards the middle of the ring
      const cx = ring.reduce((s, v) => s + pos.get(v)[0], 0) / ring.length, cy = ring.reduce((s, v) => s + pos.get(v)[1], 0) / ring.length;
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
      const sgn = (cx - mx) * nx + (cy - my) * ny >= 0 ? 1 : -1;
      const o = 0.17 * L, sh = 0.13;
      line(x1, y1, x2, y2);
      line(x1 + nx * sgn * o + (x2 - x1) * sh, y1 + ny * sgn * o + (y2 - y1) * sh, x2 + nx * sgn * o - (x2 - x1) * sh, y2 + ny * sgn * o - (y2 - y1) * sh);
    } else { // centred double bond
      const o = 0.07 * L;
      line(x1 + nx * o, y1 + ny * o, x2 + nx * o, y2 + ny * o); line(x1 - nx * o, y1 - ny * o, x2 - nx * o, y2 - ny * o);
    }
  });

  atoms.forEach((a, k) => {
    if (!labelled[k]) return;
    const [x, y] = pos.get(k);
    const color = COLORS[a.el] || "currentColor";
    const nbs = adj[k].map(({ to }) => pos.get(to));
    const avgDx = nbs.length ? nbs.reduce((s, p) => s + (p[0] - x), 0) / nbs.length : 0;
    const common = { "font-size": FS, "font-family": "Arial, Helvetica, sans-serif", "font-weight": "600", fill: color, stroke: "none" };
    g.append(el("text", { ...common, x, y: y + FS * 0.35, "text-anchor": "middle" }, a.el));
    const w = a.el.length * FS * 0.6;
    let hText = a.h > 0 ? "H" + (a.h > 1 ? sub(a.h) : "") : "";
    if (hText) {
      const right = nbs.length ? avgDx <= 0 : false;
      g.append(el("text", { ...common, x: right ? x + w / 2 + 1 : x - w / 2 - 1, y: y + FS * 0.35, "text-anchor": right ? "start" : "end" }, hText));
    }
    if (a.charge) {
      const mag = Math.abs(a.charge) > 1 ? String(Math.abs(a.charge)) : "";
      const hShift = hText && avgDx <= 0 ? (hText.length) * FS * 0.6 : 0;
      g.append(el("text", { ...common, "font-size": FS * 0.8, x: x + w / 2 + 1 + hShift, y: y - FS * 0.3, "text-anchor": "start" }, mag + (a.charge > 0 ? "+" : "−")));
    }
  });
  return svg;
}
