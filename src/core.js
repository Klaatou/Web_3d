// ===== core partagé (viewer + export) =====
const FOLIAGE_KEYS = ['leaf','foliage','feuill','canopy','crown','branch','tree','bush','plant','palm','herbe','grass'];
const TRUNK_KEYS = ['bark','trunk','tronc','ecorce'];

function nameHas(name, tokens) {
  if (!name || !tokens.length) return false;
  const low = name.toLowerCase();
  const words = name.replace(/([a-z0-9])([A-Z])/g, '$1 $2').toLowerCase().split(/[^a-z0-9\u00e0-\u00ff]+/).filter(Boolean);
  const compact = words.join('');
  return tokens.some(t => t[0] === '=' ? low === t.slice(1) : (/[^a-z0-9\u00e0-\u00ff]/.test(t) ? low.includes(t) : (compact.startsWith(t) || words.some(w => w.startsWith(t)))));
}
// v36 : disposition du clavier. La marche garde les codes physiques (KeyW, KeyA, KeyS, KeyD : Z Q S D sur AZERTY, W A S D sur QWERTY) ;
// l'aide affiche les lettres RÉELLES. Réglage 'auto' (navigator.keyboard.getLayoutMap() si présent, sinon la langue du navigateur), 'azerty' ou 'qwerty'.
const KB = {
  pref: 'auto', detected: null, listeners: [],
  byLang() { const l = String((typeof navigator !== 'undefined' && (navigator.language || (navigator.languages || [])[0])) || ''); return /^fr(-(fr|be))?$/i.test(l) ? 'azerty' : 'qwerty'; },
  layout() { return this.pref === 'azerty' || this.pref === 'qwerty' ? this.pref : (this.detected || this.byLang()); },
  keys() { return this.layout() === 'azerty' ? { fwd: 'Z', left: 'Q', back: 'S', right: 'D' } : { fwd: 'W', left: 'A', back: 'S', right: 'D' }; },
  setPref(v) { this.pref = v === 'azerty' || v === 'qwerty' ? v : 'auto'; for (const f of this.listeners) { try { f(); } catch (_) {} } },
  detect() {
    try {
      if (typeof navigator !== 'undefined' && navigator.keyboard && navigator.keyboard.getLayoutMap) navigator.keyboard.getLayoutMap().then(m => {
        const w = m.get('KeyW'), q = m.get('KeyQ');
        const d = (w === 'z' || q === 'a') ? 'azerty' : ((w === 'w' && q === 'q') ? 'qwerty' : null);
        if (d && d !== this.detected) { this.detected = d; for (const f of this.listeners) { try { f(); } catch (_) {} } }
      }).catch(() => {});
    } catch (_) {}
  }
};
KB.detect();
// v39 : diagnostic à copier (bouton « Copier le diagnostic » de la page et du viewer) : état technique, durées des tuiles et 10 dernières erreurs.
// Jamais d'adresse de serveur (remplacée par ADRESSE) ni la partie # de l'adresse (pseudo, clé).
const DIAG = { errs: [] };
DIAG.mask = s => String(s).replace(/data:[^,\s]*,[^\s)]*/g, 'data:…').replace(/\b([a-z][a-z0-9+.-]*:\/\/)[^\/\s'"<>)]+/gi, '$1ADRESSE');
DIAG.str = x => {
  if (x && typeof x === 'object' && (x.message || x.stack)) {
    const at = String(x.stack || '').split('\n').map(l => l.trim()).filter(l => /^at |@/.test(l)).slice(0, 2);
    return String(x.message || x) + (at.length ? ' | ' + at.join(' | ') : '');
  }
  if (typeof x === 'string') return x;
  try { return JSON.stringify(x); } catch (_) { return String(x); }
};
DIAG.note = (kind, ...a) => {
  try {
    const s = DIAG.mask(a.map(DIAG.str).join(' ')).replace(/\b\d{1,3}(\.\d{1,3}){3}\b/g, 'ADRESSE').slice(0, 500);
    DIAG.errs.push((performance.now() / 1000).toFixed(1) + ' s [' + kind + '] ' + s);
    if (DIAG.errs.length > 10) DIAG.errs.shift();
  } catch (_) {}
};
if (typeof window !== 'undefined' && !window.__web3dDiag) {
  window.__web3dDiag = DIAG;
  addEventListener('error', e => {
    const t = e.target;
    if (t && t !== window && t.tagName) DIAG.note('load', t.tagName.toLowerCase() + ' ' + (t.currentSrc || t.src || t.href || ''));
    else DIAG.note('error', e.error || ((e.message || '') + (e.filename ? ' (' + e.filename + ':' + e.lineno + ')' : '')));
  }, true);
  addEventListener('unhandledrejection', e => DIAG.note('promise', e.reason));
  for (const k of ['error', 'warn']) { const f = console[k]; console[k] = function (...a) { DIAG.note(k, ...a); return f.apply(this, a); }; }
}
// v40 : manuel complet sur GitHub, dans la langue de la page (français, sinon anglais)
const manualUrl = () => 'https://github.com/Klaatou/Web_3d/blob/main/docs/' + (LANG === 'fr' ? 'fr/MANUEL.md' : 'en/MANUAL.md');
// nom du moteur de rendu WebGL (carte graphique, ou moteur logiciel)
function gpuName(r) {
  let gpu = '?';
  try {
    const gl = r.getContext(); gpu = String(gl.getParameter(gl.RENDERER) || '?');
    if (/^WebKit WebGL$|^Mozilla$/i.test(gpu)) { const ext = gl.getExtension('WEBGL_debug_renderer_info'); if (ext) gpu = String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)); }
  } catch (_) {}
  return gpu;
}
// v42 : rendu sans carte graphique (moteur logiciel) : la page propose le rendu léger
const softGpu = r => /Basic Render|SwiftShader|llvmpipe|softpipe|Software/i.test(gpuName(r));
// texte du diagnostic ; extra = { cfgVersion, lines } : version de la configuration de la région, lignes d'état propres à la page ou au viewer
function diagText(viewer, extra) {
  const x = extra || {}, L = (k, v) => tr('core.diag.line', k, v), out = [tr('core.diag.title')];
  const nb = (v, d) => (Number.isFinite(v) ? i18nNum(v, d || 0) : '?');   // nombres à la manière de la langue (virgule en français)
  out.push(L(tr('core.diag.version'), '__VERSION__' + (x.cfgVersion && x.cfgVersion !== '__VERSION__' ? ' ; ' + tr('core.diag.cfgver', x.cfgVersion) : '')));
  out.push(L(tr('core.diag.date'), new Date().toLocaleString(({ fr: 'fr-FR', en: 'en-GB' })[LANG]) + ' ; ' + tr('core.diag.uptime', nb(performance.now() / 1000))));
  out.push(L(tr('core.diag.page'), location.protocol + (location.host ? '//ADRESSE' : '//') + location.pathname + location.search));
  out.push(L(tr('core.diag.lang'), LANG + ' · ' + ((navigator.languages || []).join(',') || navigator.language || '?') + ' · ' + KB.layout().toUpperCase()));
  out.push(L(tr('core.diag.browser'), navigator.userAgent));
  const r = viewer && viewer.renderer;
  out.push(L(tr('core.diag.screen'), tr('core.diag.screen.v', innerWidth, innerHeight, nb(devicePixelRatio, 2), r ? nb(r.getPixelRatio(), 2) : '?')));
  if (r) {
    const gpu = gpuName(r);
    out.push(L(tr('core.diag.gpu'), tr('core.diag.gpu.v', gpu, r.capabilities && r.capabilities.isWebGL2 ? 2 : 1, r.capabilities ? r.capabilities.maxTextureSize : '?')));
    const i = r.info || {}, ri = i.render || {}, mi = i.memory || {};
    out.push(L(tr('core.diag.render'), tr('core.diag.render.v', ri.triangles, ri.calls, mi.geometries, mi.textures, (i.programs || []).length)));
  }
  if (viewer && viewer.cfg && viewer.renderStats) {
    // v42 : réglages du rendu léger en cours, images rendues sur les 5 dernières secondes et ce qui force le rendu continu
    const c = viewer.cfg, s = viewer.renderStats(), yn = v => (v ? tr('common.yes') : tr('common.no'));
    const rad = viewer.tiled && viewer.tilesState ? nb(viewer.tilesState().radius) + ' m' : '\u2014';
    out.push(L(tr('core.diag.light'), tr('core.diag.light.v', nb(Math.round((Number(c.pixelScale) > 0 ? Number(c.pixelScale) : 1) * 100)), Number(c.fpsMax) > 0 ? nb(Number(c.fpsMax)) : tr('core.diag.light.nolimit'), yn(!!c.ovOnly), rad, yn(c.antialias !== false))));
    const why = { sea: tr('core.diag.cause.sea'), peers: tr('core.diag.cause.peers'), walk: tr('core.diag.cause.walk'), tiles: tr('core.diag.cause.tiles') };
    out.push(L(tr('core.diag.fps'), tr('core.diag.fps.v', nb(s.rate, 1), s.causes.length ? s.causes.map(k => why[k]).join(', ') : tr('core.diag.cause.none'))));
  }
  const pm = performance.memory;
  out.push(L(tr('core.diag.mem'), pm && pm.usedJSHeapSize ? tr('core.diag.mem.v', nb(pm.usedJSHeapSize / 1048576), nb(pm.jsHeapSizeLimit / 1048576)) : tr('core.diag.na')));
  if (viewer && viewer.tiled && viewer.tilesState) {
    try {
      const s = viewer.tilesState(), ok = (s.log || []).filter(l => l.ok);
      out.push(L(tr('core.diag.tiles'), tr('core.diag.tiles.v', s.loaded, s.total, s.loading, s.failed)));
      if (ok.length) {
        const med = k => { const v = ok.map(l => l[k]).filter(Number.isFinite).sort((a, b) => a - b); return v.length ? v[v.length >> 1] + ' / ' + v[v.length - 1] : '?'; };
        out.push(L(tr('core.diag.times'), tr('core.diag.times.v', nb(ok[0].at / 1000, 1), nb(ok[ok.length - 1].at / 1000, 1), med('totalMs'), med('downloadMs'), med('parseMs'))));
      }
      if ((s.failedFiles || []).length) out.push(L(tr('core.diag.failed'), s.failedFiles.slice(0, 5).join(', ') + (s.failedFiles.length > 5 ? ' …' : '')));
    } catch (_) {}
  }
  if ((x.lines || []).length) { out.push('', tr('core.diag.state')); for (const l of x.lines) out.push('  ' + l); }
  out.push('', tr('core.diag.errors', DIAG.errs.length));
  if (DIAG.errs.length) for (const e of DIAG.errs) out.push('  ' + e); else out.push('  ' + tr('core.diag.noerror'));
  return DIAG.mask(out.join('\n'));
}
// la lettre imprimée par la touche (minuscule) : M, comme toute touche dont la place change d'une disposition à l'autre, se reconnaît à cette lettre et non au code physique
const keyChar = e => (typeof e.key === 'string' && e.key.length === 1 ? e.key.toLowerCase() : '');
function parseIgnore(s) { return String(s || '').toLowerCase().split(/[,;]+/).map(x => x.trim()).filter(Boolean); }

function describeObject(o) {
  const sz = new THREE.Box3().setFromObject(o).getSize(new THREE.Vector3());
  const parents = []; for (let q = o.parent; q; q = q.parent) if (q.name) parents.push(q.name);
  const mats = (Array.isArray(o.material) ? o.material : [o.material]).map(m => m && m.name).filter(Boolean);
  const token = o.name || parents[0] || mats[0] || '';
  return {
    name: token, mesh: o.name || '', parents, materials: mats, token, size: sz.toArray(),
    text: tr('core.pick.mesh', o.name || tr('core.pick.noname')) + '\n' + tr('core.pick.parents', parents.slice(0, 3).join(' › ') || tr('core.pick.none')) + '\n' + tr('core.pick.material', mats.join(', ') || tr('core.pick.noname')) + '\n' + tr('core.pick.size', sz.toArray().map(v => v.toFixed(2)).join(' × '))
  };
}

// description d'un clic : nom de l'élément + point touché (x, y, z, 2 décimales)
function describePick(o, point) {
  const d = describeObject(o);
  if (point) { d.point = point; d.text += '\n' + tr('core.pick.point', point.map(v => v.toFixed(2)).join(', ')); }
  return d;
}

// Référence d'un élément pour le champ mesh d'une zone. Nom unique dans le modèle : le nom. Nom partagé par plusieurs objets
// (OAR : des dizaines de prims s'appellent pareil) : « nom#index », index = rang de l'objet parmi les objets de ce nom dans l'ordre
// de parcours (pré-ordre, enfants dans l'ordre du fichier). glb2html.py applique la même règle (resolve_mesh_ref).
function nodesNamed(root, name) { const out = []; root.traverse(o => { if (o.name === name) out.push(o); }); return out; }
function meshRefOf(root, o) {
  const same = nodesNamed(root, o.name);
  return same.length > 1 ? o.name + '#' + same.indexOf(o) : o.name;
}
// objets désignés par une référence : le nom exact d'abord (zones anciennes), sinon « base#index »
function resolveMeshRef(root, ref) {
  if (!root || !ref) return [];
  const exact = nodesNamed(root, ref);
  if (exact.length) return exact;
  const m = /^(.*)#(\d+)$/.exec(ref);
  if (!m) return [];
  const o = nodesNamed(root, m[1])[Number(m[2])];
  return o ? [o] : [];
}

function isIgnoredMesh(o, tokens) {
  if (!tokens.length) return false;
  for (let p = o; p; p = p.parent) if (nameHas(p.name, tokens)) return true;
  const mats = Array.isArray(o.material) ? o.material : [o.material];
  return mats.length > 0 && mats.every(m => !m || nameHas(m.name, tokens));
}

function isFoliageName(n) {
  n = (n || '').toLowerCase();
  return !TRUNK_KEYS.some(k => n.includes(k)) && FOLIAGE_KEYS.some(k => n.includes(k));
}

// Grille XZ de triangles (monde) pour sol et murs : exclut le feuillage.
// Générateur : rend la main toutes les quelques milliers de triangles (mode tuiles : construction par tranches, sans figer l'image) ;
// buildCollisionGrid l'exécute d'une traite (promenade ordinaire, résultat identique).
function buildCollisionGrid(root, cell = 3, tokens = []) {
  const it = collisionGridSteps(root, cell, tokens);
  let r; do { r = it.next(); } while (!r.done);
  return r.value;
}
function* collisionGridSteps(root, cell = 3, tokens = []) {
  let work = 0;
  const meshes = []; let total = 0;
  root.traverseVisible(o => {
    if (!o.isMesh || o.isInstancedMesh || o.isSkinnedMesh || !o.geometry || !o.geometry.attributes.position) return;
    if (tokens.length) for (let p = o; p; p = p.parent) if (nameHas(p.name, tokens)) return;
    const g = o.geometry, cnt = Math.floor((g.index ? g.index.count : g.attributes.position.count) / 3);
    const isArr = Array.isArray(o.material), mats = isArr ? o.material : [o.material];
    const skipMat = m => !m || isFoliageName(m.name) || nameHas(m.name, tokens);
    if (mats.every(skipMat)) return;
    let ranges;
    if (isArr && g.groups.length) {
      ranges = [];
      for (const gr of g.groups) {
        const m = mats[gr.materialIndex];
        if (skipMat(m)) continue;
        const s = Math.floor(gr.start / 3), e = Math.min(Math.floor((gr.start + gr.count) / 3), cnt);
        if (e > s) ranges.push([s, e]);
      }
    } else ranges = [[0, cnt]];
    for (const r of ranges) total += r[1] - r[0];
    meshes.push({ o, g, ranges });
  });
  const T = new Float32Array(total * 9); let t = 0;
  const v = new THREE.Vector3();
  for (const { o, g, ranges } of meshes) {
    o.updateWorldMatrix(true, false);
    const M = o.matrixWorld, p = g.attributes.position, ix = g.index;
    for (const [s, e] of ranges) for (let i = s; i < e; i++, t++) {
      if ((++work & 4095) === 0) yield;
      for (let k = 0; k < 3; k++) {
        v.fromBufferAttribute(p, ix ? ix.getX(i * 3 + k) : i * 3 + k).applyMatrix4(M);
        T[t * 9 + k * 3] = v.x; T[t * 9 + k * 3 + 1] = v.y; T[t * 9 + k * 3 + 2] = v.z;
      }
    }
  }
  const cells = new Map(), big = [];
  const key = (ix, iz) => (ix + 32768) * 65536 + (iz + 32768);
  for (let i = 0; i < total; i++) {
    if ((++work & 2047) === 0) yield;
    const b = i * 9;
    const minX = Math.min(T[b], T[b + 3], T[b + 6]), maxX = Math.max(T[b], T[b + 3], T[b + 6]);
    const minZ = Math.min(T[b + 2], T[b + 5], T[b + 8]), maxZ = Math.max(T[b + 2], T[b + 5], T[b + 8]);
    if (!(maxX - minX < 1e7) || !(maxZ - minZ < 1e7)) continue;
    const x0 = Math.floor(minX / cell), x1 = Math.floor(maxX / cell), z0 = Math.floor(minZ / cell), z1 = Math.floor(maxZ / cell);
    if ((x1 - x0 + 1) * (z1 - z0 + 1) > 400) { big.push(i); continue; }
    for (let ix = x0; ix <= x1; ix++) for (let iz = z0; iz <= z1; iz++) {
      const k = key(ix, iz); let a = cells.get(k);
      if (!a) { a = []; cells.set(k, a); }
      a.push(i);
    }
  }
  // hauteur du sol la plus haute <= y0 en (x,z), sinon null
  function ground(x, z, y0) {
    let best = -Infinity;
    const test = i => {
      const b = i * 9;
      const ax = T[b], ay = T[b + 1], az = T[b + 2], bx = T[b + 3], by = T[b + 4], bz = T[b + 5], cx = T[b + 6], cy = T[b + 7], cz = T[b + 8];
      const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
      if (Math.abs(d) < 1e-9) return;
      const l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d;
      const l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d;
      const l3 = 1 - l1 - l2;
      if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) return;
      const y = l1 * ay + l2 * by + l3 * cy;
      if (y <= y0 + 1e-4 && y > best) best = y;
    };
    const list = cells.get(key(Math.floor(x / cell), Math.floor(z / cell)));
    if (list) for (let i = 0; i < list.length; i++) test(list[i]);
    for (let i = 0; i < big.length; i++) test(big[i]);
    return best === -Infinity ? null : best;
  }
  // premier mur franchi par le rayon horizontal (dx,dz unitaire) sur dist : {t,nx,nz} ou null
  function wall(x, y, z, dx, dz, dist) {
    const ex = x + dx * dist, ez = z + dz * dist;
    const x0 = Math.floor(Math.min(x, ex) / cell), x1 = Math.floor(Math.max(x, ex) / cell);
    const z0 = Math.floor(Math.min(z, ez) / cell), z1 = Math.floor(Math.max(z, ez) / cell);
    let bestT = Infinity, bn = null;
    const test = i => {
      const b = i * 9;
      const ax = T[b], ay = T[b + 1], az = T[b + 2];
      const e1x = T[b + 3] - ax, e1y = T[b + 4] - ay, e1z = T[b + 5] - az;
      const e2x = T[b + 6] - ax, e2y = T[b + 7] - ay, e2z = T[b + 8] - az;
      const nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
      const nl = Math.hypot(nx, ny, nz);
      if (nl < 1e-12 || Math.hypot(nx, nz) / nl < 0.3) return; // sols / pentes douces : pas des murs
      // Möller–Trumbore, direction (dx,0,dz)
      const px = -dz * e2y, py = dz * e2x - dx * e2z, pz = dx * e2y;
      const det = e1x * px + e1y * py + e1z * pz;
      if (Math.abs(det) < 1e-9) return;
      const inv = 1 / det, tx = x - ax, ty = y - ay, tz = z - az;
      const u = (tx * px + ty * py + tz * pz) * inv;
      if (u < 0 || u > 1) return;
      const qx = ty * e1z - tz * e1y, qy = tz * e1x - tx * e1z, qz = tx * e1y - ty * e1x;
      const w = (dx * qx + dz * qz) * inv;
      if (w < 0 || u + w > 1) return;
      const tt = (e2x * qx + e2y * qy + e2z * qz) * inv;
      if (tt >= 0 && tt <= dist && tt < bestT) { bestT = tt; bn = { t: tt, nx, nz }; }
    };
    for (let ix = x0; ix <= x1; ix++) for (let iz = z0; iz <= z1; iz++) {
      const list = cells.get(key(ix, iz));
      if (list) for (let i = 0; i < list.length; i++) test(list[i]);
    }
    for (let i = 0; i < big.length; i++) test(big[i]);
    return bn;
  }
  return { count: total, ground, wall };
}

const SEA_VERT = `
uniform float uTime, uAmp, uHoleRadius, uHoleFade;
uniform vec2 uHoleCenter;
varying float vWave;
void main(){
  vec3 pos = position;
  float edge = smoothstep(uHoleRadius - uHoleFade, uHoleRadius + uHoleFade, length(pos.xy - uHoleCenter));
  float w1 = sin(pos.x * 0.03 + uTime) * 0.8;
  float w2 = cos(pos.y * 0.025 + uTime * 0.7) * 0.6;
  float w3 = sin(pos.x * 0.012 + pos.y * 0.012 + uTime * 0.5) * 0.35;
  float wave = ((w1 + w2) * uAmp + w3 * uAmp * 0.6) * edge;
  pos.z += wave;
  vWave = wave;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}`;
const SEA_FRAG = `
uniform vec3 uColor;
varying float vWave;
void main(){
  gl_FragColor = vec4(uColor + vWave * 0.03, 1.0);
  #include <colorspace_fragment>
}`;

function disposeObject(root) {
  root.traverse(o => {
    if (o.geometry) o.geometry.dispose();
    if (!o.material) return;
    for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
      if (!m) continue;
      for (const k in m) { const v = m[k]; if (v && v.isTexture) v.dispose(); }
      m.dispose();
    }
  });
}

// v43 : valeurs du repère des zones en anglais (dot, range, none) ; les anciennes (discret, portee, aucun) restent lues
const ZM_OLD = { discret: 'dot', portee: 'range', aucun: 'none' };
const zmNorm = v => ZM_OLD[v] || v;
function createViewer(container, cfg0, loader) {
  const cfg = Object.assign({}, cfg0);
  if (cfg.zoneMarker) cfg.zoneMarker = zmNorm(cfg.zoneMarker);
  let onMouse = null, onView = null, onFly = null, onCfg = null, onWalk = null, onPick = null, onPresence = null, onChat = null, onHistory = null, onBlink = null, onBlinkEnd = null, onPeer = null, onName = null, spectateOn = false, pickOrbit = false, walking = false, linkLock = false;
  const W = { pos: new THREE.Vector3(), spawn: new THREE.Vector3(), vy: 0, grounded: true, yaw: 0, pitch: 0, keys: new Set(), jumpReq: false, drag: false, mouseFree: false, saved: null, grid: null,
    fly: false, flyFloor: undefined, view: 'fps', cam: new THREE.Vector3(), cyaw: 0, cpitch: 0,
    tyaw: 0, tpitch: 0,   // v35 : caméra à la troisième personne (orbite propre) ; W.yaw reste l'orientation de l'avatar
    run: new Set(), tap: {}, upT: 0, moved: false,
    tdist: (() => { let d = 4; try { const v = parseFloat(localStorage.getItem('glb2html_tpsDist')); if (v >= 1 && v <= 30) d = v; } catch (_) {} return d; })() };   // v35 : distance de la caméra à la troisième personne (1 à 30 m, mémorisée)
  let home = null;   // v33 : point de retour { pos, yaw, forF } (arrivée « default » ou cible de départ)
  let model = null, modelRot = 0, fit = 1, sea = null, seaMat = null, dirty = true, foliageMats = [];
  let seaCx = 0, seaCz = 0;   // centre de la mer : l'origine, ou le centre de la région en mode tuiles

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(cfg.skyColor);
  scene.fog = new THREE.Fog(cfg.skyColor, 1500, 4500);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 5000);
  camera.position.set(0, 22, 45);

  const renderer = new THREE.WebGLRenderer({ antialias: cfg.antialias !== false, powerPreference: 'high-performance' });   // v42 : anticrénelage fixé à la création du contexte (rendu léger : pris au chargement)
  renderer.sortObjects = false;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.shadowMap.enabled = false;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.fromArray(cfg.target);
  controls.enableDamping = true;
  controls.dampingFactor = 0.1;
  controls.minDistance = 1;
  controls.maxDistance = 2000;
  const BASE = { far: camera.far, fogNear: scene.fog.near, fogFar: scene.fog.far, maxDist: controls.maxDistance };   // rétablis par closeTiles()
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.addEventListener('change', () => { dirty = true; });

  scene.add(new THREE.AmbientLight(0xffffff, 1.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.8); sun.position.set(120, 200, 80); scene.add(sun);
  const sun2 = new THREE.DirectionalLight(0xffffff, 0.7); sun2.position.set(-80, 100, -120); scene.add(sun2);
  const hemi = new THREE.HemisphereLight(cfg.skyColor, 0xffe8b0, 0.8); scene.add(hemi);

  function resize() {
    const w = container.clientWidth || innerWidth, h = container.clientHeight || innerHeight;
    const ps = Number(cfg.pixelScale), k = ps > 0 ? Math.min(1, Math.max(0.25, ps)) : 1;   // v42 : résolution du rendu (rendu léger) ; le navigateur agrandit l'image
    renderer.setPixelRatio((cfg.retina ? Math.min(Math.max(window.devicePixelRatio || 1, 2), 3) : 1) * k);
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    dirty = true;
  }
  new ResizeObserver(resize).observe(container);
  resize();

  function buildSea() {
    if (sea) { scene.remove(sea); sea.geometry.dispose(); seaMat.dispose(); sea = null; seaMat = null; }
    if (cfg.sea) {
      const seg = cfg.anim ? cfg.seaSegments : 1;
      const geo = new THREE.PlaneGeometry(cfg.seaSize, cfg.seaSize, seg, seg);
      if (cfg.anim) {
        seaMat = new THREE.ShaderMaterial({
          uniforms: {
            uTime: { value: 0 }, uAmp: { value: cfg.wave },
            uHoleRadius: { value: cfg.hole }, uHoleFade: { value: cfg.holeFade },
            uHoleCenter: { value: new THREE.Vector2(cfg.holeX, -cfg.holeZ) },
            uColor: { value: new THREE.Color(cfg.seaColor) }
          },
          vertexShader: SEA_VERT, fragmentShader: SEA_FRAG, side: THREE.FrontSide
        });
      } else {
        seaMat = new THREE.MeshStandardMaterial({ color: cfg.seaColor, roughness: 0.6, metalness: 0.1, side: THREE.DoubleSide });
      }
      seaMat.fog = false;
      seaMat.polygonOffset = true; seaMat.polygonOffsetFactor = -2; seaMat.polygonOffsetUnits = -2;
      sea = new THREE.Mesh(geo, seaMat);
      sea.rotation.x = -Math.PI / 2;
      sea.position.set(seaCx, cfg.seaY, seaCz);
      sea.frustumCulled = false;
      sea.renderOrder = -10;
      sea.userData.isSea = true;
      scene.add(sea);
    }
    dirty = true;
  }
  buildSea();

  function fixMaterials(root, append) {
    if (!append) foliageMats = [];
    root.traverse(o => {
      if (!o.isMesh || !o.material) return;
      let foliageMesh = false;
      for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
        if (!m) continue;
        const n = (m.name || '').toLowerCase();
        const trunk = TRUNK_KEYS.some(k => n.includes(k));
        const foliage = !trunk && FOLIAGE_KEYS.some(k => n.includes(k));
        if (m.map) m.map.colorSpace = THREE.SRGBColorSpace;
        if (m.emissiveMap) m.emissiveMap.colorSpace = THREE.SRGBColorSpace;
        if (foliage) {
          foliageMesh = true;
          foliageMats.push(m);
          m.transparent = false; m.depthWrite = true; m.side = THREE.DoubleSide;
          m.alphaTest = cfg.foliageCutout; m.alphaToCoverage = true; m.fog = false;
        } else {
          if (trunk) m.side = THREE.FrontSide;
          if (m.emissive && !m.emissiveMap && m.emissive.getHex() !== 0 && (trunk || !(n.includes('light') || n.includes('emit')))) {
            m.emissive.setHex(0); m.emissiveIntensity = 0;
          }
        }
        if (m.isMeshStandardMaterial && !m.roughness) m.roughness = 0.75;
        m.needsUpdate = true;
      }
      o.castShadow = o.receiveShadow = false;
      o.renderOrder = foliageMesh ? 2 : 0;
    });
  }

  function frame(camDir = cfg.camDir, target = cfg.target, zoom = cfg.zoom) {
    const dir = new THREE.Vector3().fromArray(camDir).normalize();
    controls.target.fromArray(target);
    camera.position.copy(controls.target).addScaledVector(dir, fit * zoom);
    controls.update();
    dirty = true;
  }

  function setModel(root) {
    if (walking) walkStop();
    landY = null; landKey = '';
    if (model) { scene.remove(model); disposeObject(model); }
    model = root;
    fixMaterials(root);
    // rotation de la région autour de l'axe vertical : AVANT recentrage, boîte englobante, sol de promenade et capture de vignette
    modelRot = rotDeg();
    if (modelRot) root.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(UPV, modelRot * Math.PI / 180));
    root.updateMatrixWorld(true);
    // centre = moyenne des origines de meshes, puis y+15
    const sum = new THREE.Vector3(), wp = new THREE.Vector3(); let cnt = 0;
    root.traverse(o => { if (o.isMesh) { o.getWorldPosition(wp); sum.add(wp); cnt++; } });
    const center = cnt ? sum.divideScalar(cnt) : new THREE.Box3().setFromObject(root).getCenter(new THREE.Vector3());
    root.position.sub(center); root.position.y += 15;
    root.updateMatrixWorld(true);
    root.traverse(o => { if (o.isMesh) { o.updateMatrix(); o.matrixAutoUpdate = false; } });
    scene.add(root);
    if (zones.length) { resolveLinks(); buildZones(); }
    const size = new THREE.Box3().setFromObject(root).getSize(new THREE.Vector3());
    fit = Math.max(size.x, size.y, size.z) / 2 / Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) * 1.35 || 1;
    frame();
  }

  // 0, 90, 180 ou 270 (autre valeur : arrondie au quart de tour le plus proche)
  function rotDeg() { return ((Math.round((Number(cfg.rotate) || 0) / 90) * 90) % 360 + 360) % 360; }
  // aligne le modèle déjà chargé sur cfg.rotate : rotation autour de l'axe vertical passant par le centre de la région (origine)
  function applyRotation() {
    if (!model || TL.on) return;
    const d = rotDeg() - modelRot;
    if (!d) return;
    const q = new THREE.Quaternion().setFromAxisAngle(UPV, d * Math.PI / 180);
    model.quaternion.premultiply(q); model.position.applyQuaternion(q);
    modelRot = rotDeg();
    model.updateMatrixWorld(true);
    model.traverse(o => { if (o.isMesh) o.updateMatrix(); });
    if (zones.length) { resolveLinks(); buildZones(); }
    if (walking) W.grid = buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore));
    landKey = ''; dirty = true;
  }

  async function loadBuffer(buf) {
    const gltf = await loader.parseAsync(buf, '');
    setModel(gltf.scene);
    return gltf;
  }

  // ---- mode tuiles (champ cfg.tiles) : région découpée par tools/glb2tiles.py (X.tiles.json, docs/fr/MANUEL.md § 17 bis)
  // Les tuiles dont la boîte est proche de l'avatar (en vue globale : de la cible) sont chargées, les lointaines déchargées. Repère = celui du
  // modèle d'origine (aucun recentrage) ; la rotation de la région est appliquée à la racine des tuiles. Une grille de collision par tuile.
  // Zones liées à un élément (champ mesh) : ignorées (la référence nom#index se calcule sur tout le modèle).
  const TL = { on: !!cfg.tiles, src: null, refs: false, refsKnown: false, refIndex: new Map(), linkDirty: false, linkSig: '', root: null, tiles: [], extent: null, inflight: 0, gridQ: [], pending: null, forced: null, forcedUntil: 0,
    waitT: -1e9, waitAt: null, waitSince: 0, anchor: null, log: [], lastUpd: 0, infoKey: '', onInfo: null, onError: null, lastError: '', radius: 150, margin: 60, maxBytes: 200 * 1048576, maxTri: 8e6, conc: 4 };
  // v33 : budget de temps (ms par image) de la construction des grilles de collision : normal, et généreux pour la tuile que l'avatar (ou l'arrivée demandée) attend
  const GRID_MS = 6, GRID_MS_PRIO = 40;
  // vue d'ensemble (X.overview.glb, champ « overview » de X.tiles.json) : un nœud par fichier de tuile, masqué dès que la tuile détaillée est affichée
  // (groupe ajouté à la racine des tuiles) et réaffiché quand elle est déchargée. Jamais utilisée pour les collisions, le sol ni le budget des tuiles.
  const OV = { root: null, bytes: 0, tri: 0, cells: 0, state: 'none' };
  const ovSync = t => { if (t.ov) { const v = !t.grp; if (t.ov.visible !== v) { t.ov.visible = v; dirty = true; } } };
  const ovCells = () => OV.root ? OV.root.children.filter(c => c.visible) : [];
  const TILE_M = 0.5;   // tolérance (m) des tests « le point est dans la boîte de la tuile »
  const safeRel = p => typeof p === 'string' && p !== '' && p.length < 400 && !/^[\/\\]/.test(p) && !/[\\:?#\u0000-\u001f]/.test(p) && !p.split('/').some(s => s === '' || s === '..');
  const relUrl = (p, base) => new URL(p.split('/').map(encodeURIComponent).join('/'), base);
  // source des fichiers d'une région en tuiles : http relatif à la page (coquille, viewer avec ?tiles=) ; le viewer en fournit une autre pour un dossier choisi
  const urlSource = () => ({
    async json(rel) { const r = await fetch(relUrl(rel, location.href).href, { cache: 'no-store' }); if (!r.ok) throw new Error(rel + ' : HTTP ' + r.status); return r.json(); },
    async buf(rel, signal) { const r = await fetch(relUrl(rel, location.href).href, signal ? { signal } : {}); if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); }
  });
  // références d'objets (extras.ref écrit par glb2tiles v32) : index des nœuds des tuiles chargées, pour les zones liées à un objet
  const refPieces = ref => (TL.refIndex.get(ref) || []).length;
  const zoneOff = z => TL.on && TL.refs && z.mesh && z.type !== 'spawn' && !zoneLink.has(z.id);   // zone liée dont la tuile n'est pas chargée : absente
  function refsAdd(t) {
    t.refObjs = [];
    t.grp.traverse(o => {
      const r = o.userData && o.userData.ref;
      if (typeof r !== 'string') return;
      let l = TL.refIndex.get(r); if (!l) TL.refIndex.set(r, l = []);
      l.push(o); t.refObjs.push(o);
    });
    if (t.refObjs.length) TL.linkDirty = true;
  }
  function refsRemove(t) {
    if (!t.refObjs) return;
    for (const o of t.refObjs) {
      const r = o.userData.ref, l = TL.refIndex.get(r);
      if (l) { const i = l.indexOf(o); if (i >= 0) l.splice(i, 1); if (!l.length) TL.refIndex.delete(r); }
    }
    if (t.refObjs.length) TL.linkDirty = true;
    t.refObjs = null;
  }
  const linkSignature = () => zones.filter(z => z.mesh && z.type !== 'spawn').map(z => z.id + ':' + refPieces(z.mesh)).join('|');
  function relinkZones() {
    if (!TL.on || !TL.refs) return;
    const sig = linkSignature();
    if (sig === TL.linkSig) return;
    resolveLinks(); buildZones();
    if (selId) zoneSelect(selId);
  }
  // fin du mode tuiles (le viewer ouvre un autre fichier) : tout est libéré, caméra, brouillard et distance maximale d'origine
  function closeTiles() {
    if (walking) walkStop();
    for (const t of TL.tiles) { if (t.ac) { try { t.ac.abort(); } catch (e) {} t.ac = null; } }
    if (TL.root) { for (const t of TL.tiles) if (t.grp) tileUnload(t); scene.remove(TL.root); if (model === TL.root) model = null; }
    if (OV.root) { scene.remove(OV.root); disposeObject(OV.root); }
    OV.root = null; OV.bytes = OV.tri = OV.cells = 0; OV.state = 'none';
    TL.tiles = []; TL.root = null; TL.gridQ = []; TL.pending = null; TL.forced = null; TL.anchor = null; TL.waitAt = null; TL.refIndex.clear(); TL.refs = false; TL.refsKnown = false; TL.linkSig = ''; TL.src = null;
    TL.on = false;
    scene.fog.near = BASE.fogNear; scene.fog.far = BASE.fogFar; camera.far = BASE.far; camera.updateProjectionMatrix(); controls.maxDistance = BASE.maxDist;
    seaCx = seaCz = 0; if (sea) sea.position.set(0, cfg.seaY, 0);
    resolveLinks(); buildZones(); landY = null; landKey = ''; dirty = true;
  }
  const inTile = (t, x, z, m) => x >= t.box[0] - m && x <= t.box[2] + m && z >= t.box[1] - m && z <= t.box[3] + m;
  const tileDist = (t, f) => Math.hypot(Math.max(t.box[0] - f.x, 0, f.x - t.box[2]), Math.max(t.box[1] - f.z, 0, f.z - t.box[3]));
  // grille composite : sol et murs des seules tuiles prêtes ; pending(x,z) = une tuile dont la boîte contient ce point n'est pas encore prête
  const TG = {
    tiled: true,
    get count() { let n = 0; for (const t of TL.tiles) if (t.state === 'ready' && t.grid) n += t.grid.count; return n; },
    ground(x, z, y0) {
      let best = null;
      for (const t of TL.tiles) {
        if (t.state !== 'ready' || !t.grid || !inTile(t, x, z, TILE_M)) continue;
        const g = t.grid.ground(x, z, y0);
        if (g !== null && (best === null || g > best)) best = g;
      }
      return best;
    },
    wall(x, y, z, dx, dz, dist) {
      const ex = x + dx * dist, ez = z + dz * dist, x0 = Math.min(x, ex) - TILE_M, x1 = Math.max(x, ex) + TILE_M, z0 = Math.min(z, ez) - TILE_M, z1 = Math.max(z, ez) + TILE_M;
      let best = null;
      for (const t of TL.tiles) {
        if (t.state !== 'ready' || !t.grid || t.box[0] > x1 || t.box[2] < x0 || t.box[1] > z1 || t.box[3] < z0) continue;
        const h = t.grid.wall(x, y, z, dx, dz, dist);
        if (h && (!best || h.t < best.t)) best = h;
      }
      return best;
    },
    pending(x, z) { for (const t of TL.tiles) if (t.state !== 'ready' && inTile(t, x, z, TILE_M)) return true; return false; }
  };
  function disposeTile(grp) {
    const texs = new Set();
    grp.traverse(o => {
      if (o.skeleton) o.skeleton.dispose();
      if (o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m) for (const k in m) { const v = m[k]; if (v && v.isTexture) texs.add(v); }
    });
    disposeObject(grp);
    for (const t of texs) { const im = t.image; if (im && typeof im.close === 'function') { try { im.close(); } catch (e) {} } }   // libère aussi la mémoire CPU des images décodées
  }
  // tuiles qui contiennent le point (x, z) ; à défaut la plus proche dans le rayon de chargement
  function tilesAt(x, z) {
    const set = TL.tiles.filter(t => inTile(t, x, z, TILE_M));
    if (set.length) return set;
    const n = TL.tiles.map(t => [tileDist(t, { x, z }), t]).filter(a => a[0] <= TL.radius).sort((a, b) => a[0] - b[0])[0];
    return n ? [n[1]] : [];
  }
  const tileDone = t => t.state === 'ready' || t.state === 'failed';
  const anchorOpen = () => !!TL.anchor && TL.anchor.tiles.some(t => !tileDone(t));   // l'arrivée demandée attend encore une tuile
  // v33 : ce que « Chargement du sol… » attend : la tuile du téléport en attente, de l'arrivée demandée ou du point où l'avatar est arrêté
  function waitInfo(now) {
    let at, since, kind, set;
    if (TL.pending) { at = TL.pending.at; since = TL.pending.t0 || TL.waitSince; kind = 'pending'; set = tilesAt(at.x, at.z); }
    else if (anchorOpen()) { at = TL.anchor; since = TL.anchor.t0; kind = 'anchor'; set = TL.anchor.tiles; }
    else if (now - TL.waitT < 600 && TL.waitAt) { at = TL.waitAt; since = TL.waitSince; kind = 'walk'; set = tilesAt(at.x, at.z); }
    else return null;
    return { kind, ready: set.filter(t => t.state === 'ready').length, total: set.length, secs: Math.max(0, Math.floor((now - since) / 1000)), files: set.map(t => t.file) };
  }
  function tilesStatus() {
    let loaded = 0, loading = 0, failed = 0, bytes = 0, tri = 0;
    for (const t of TL.tiles) {
      if (t.state === 'ready') { loaded++; bytes += t.bytes; tri += t.tri; }
      else if (t.state === 'loading' || t.state === 'building') { loading++; bytes += t.bytes; tri += t.tri; }
      else if (t.state === 'failed') failed++;
    }
    const now = performance.now(), wait = waitInfo(now);
    return { total: TL.tiles.length, loaded, loading, failed, bytes, tri, waiting: !!TL.pending || now - TL.waitT < 600 || !!(wait && wait.kind === 'anchor'), wait, ov: { state: OV.state, bytes: OV.bytes, tri: OV.tri } };
  }
  function tilesInfo() {
    const s = tilesStatus(), w = s.wait, key = [s.loaded, s.loading, s.failed, s.bytes, s.tri, s.waiting ? 1 : 0, OV.state, OV.bytes, OV.tri, w ? w.kind + w.ready + '/' + w.total + ':' + w.secs : ''].join('|');
    if (key === TL.infoKey) return;
    TL.infoKey = key;
    if (TL.onInfo) TL.onInfo(s);
  }
  function tileFail(t, e) {
    t.state = 'failed'; t.fails = (t.fails || 0) + 1; t.retryAt = performance.now() + Math.min(30000, 3000 * Math.pow(2, t.fails - 1));
    const m = e && e.message ? e.message : String(e);
    console.warn(tr('core.tile.fail', t.file, m));
    const L = { file: t.file, ok: false, error: m, ms: Math.round(performance.now() - (t.tStart || performance.now())), at: Math.round(performance.now()) };
    TL.log.push(L); if (TL.log.length > 500) TL.log.shift();
    console.log(tr('core.tile.faillog', t.file, L.ms, m));
    if (TL.onError) TL.onError(t.file, m);
  }
  // v33 : une ligne par tuile qui devient prête (à coller dans le chat pour diagnostiquer un démarrage lent)
  function tileReady(t) {
    const now = performance.now();
    const L = { file: t.file, ok: true, bytes: t.got || t.bytes, tri: t.tri, startWaitMs: Math.round(t.tStart - (t.tWant === undefined ? t.tStart : t.tWant)), downloadMs: Math.round(t.dlMs), parseMs: Math.round(t.parseMs),
      queueMs: Math.round(t.qWait || 0), gridMs: Math.round(t.gridCpu || 0), gridWallMs: Math.round(now - t.qAt), totalMs: Math.round(now - (t.tWant === undefined ? t.tStart : t.tWant)), startAt: Math.round(t.tStart), at: Math.round(now) };
    TL.log.push(L); if (TL.log.length > 500) TL.log.shift();
    console.log(tr('core.tile.ready', t.file, (L.bytes / 1048576).toFixed(1), L.tri, L.startWaitMs, L.downloadMs, L.parseMs, L.queueMs, L.gridMs, L.gridWallMs, L.totalMs));
  }
  function tileUnload(t) {
    if (t.ac) { try { t.ac.abort(); } catch (e) {} t.ac = null; }
    const i = TL.gridQ.indexOf(t); if (i >= 0) TL.gridQ.splice(i, 1);
    if (t.grp) {
      TL.root.remove(t.grp);
      const ms = new Set(); t.grp.traverse(o => { if (o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m) ms.add(m); });
      foliageMats = foliageMats.filter(m => !ms.has(m));
      refsRemove(t);
      disposeTile(t.grp); t.grp = null;
    }
    ovSync(t);
    t.grid = null; t.gen = null; t.state = 'idle'; t.tWant = undefined; dirty = true;
  }
  async function tileStart(t) {
    const ac = new AbortController();
    t.state = 'loading'; t.ac = ac; TL.inflight++;
    t.tStart = performance.now(); t.gridCpu = 0; t.qWait = 0;
    try {
      const buf = await TL.src.buf(t.path, ac.signal);
      if (t.ac !== ac) return;
      t.dlMs = performance.now() - t.tStart; t.got = buf.byteLength;
      const tp = performance.now();
      const gltf = await loader.parseAsync(buf, '');
      t.parseMs = performance.now() - tp;
      if (t.ac !== ac) { disposeTile(gltf.scene); return; }
      const grp = gltf.scene;
      grp.name = 'tile:' + t.file;
      fixMaterials(grp, true);
      TL.root.add(grp); grp.updateMatrixWorld(true);
      grp.traverse(o => { if (o.isMesh) { o.updateMatrix(); o.matrixAutoUpdate = false; } });
      t.grp = grp; t.state = 'building';
      refsAdd(t);
      ovSync(t);   // même bloc synchrone que l'ajout du groupe : jamais d'image avec les deux, ni avec aucun des deux
      t.gen = collisionGridSteps(grp, 3, parseIgnore(cfg.walkIgnore));   // construite par tranches (tilesTick)
      t.qAt = performance.now(); t.qFirst = true;
      TL.gridQ.push(t);
      dirty = true;
    } catch (e) {
      if (t.ac === ac) { t.ac = null; tileFail(t, e); }
    } finally { TL.inflight--; tilesInfo(); }
  }
  function tilesFocus(now) {
    if (TL.pending) return TL.pending.at;
    if (walking) return { x: W.pos.x, z: W.pos.z };
    if (TL.anchor) return TL.anchor;   // v33 : l'arrivée demandée reste la référence jusqu'à la promenade (plus de délai de 4 s)
    if (TL.forced && now < TL.forcedUntil) return TL.forced;
    return { x: controls.target.x, z: controls.target.z };
  }
  function tilesUsage() {
    let bytes = 0, tri = 0, n = 0;
    for (const t of TL.tiles) if (t.state === 'loading' || t.state === 'building' || t.state === 'ready') { bytes += t.bytes; tri += t.tri; n++; }
    return { bytes, tri, n };
  }
  // choisit les tuiles à charger (rayon, plus proches d'abord) et à décharger (rayon + marge, puis budget : les plus lointaines d'abord)
  function tilesUpdate(now) {
    if (!TL.root) return;
    TL.lastUpd = now;
    // l'ancre (arrivée demandée) est lâchée dès que la cible de la vue globale a bougé : l'utilisateur regarde ailleurs
    if (TL.anchor && Math.hypot(controls.target.x - TL.anchor.tx, controls.target.z - TL.anchor.tz) > 1) TL.anchor = null;
    // v42 : rendu léger, « vue d'ensemble seule » : hors promenade (et sans promenade ni téléport en attente), aucune tuile détaillée
    if (cfg.ovOnly && (OV.state === 'ready' || OV.state === 'loading') && !walking && !TL.pending) {
      releaseAnchor(); TL.forced = null;
      for (const t of TL.tiles) if (t.state !== 'idle' && t.state !== 'failed') tileUnload(t);
      tilesInfo(); return;
    }
    const f = tilesFocus(now);
    for (const t of TL.tiles) t.d = tileDist(t, f);
    for (const t of TL.tiles) if (t.state !== 'idle' && t.state !== 'failed' && t.d > TL.radius + TL.margin) tileUnload(t);
    let want = TL.tiles.filter(t => t.d <= TL.radius && (t.state === 'idle' || (t.state === 'failed' && now >= t.retryAt))).sort((a, b) => a.d - b.d);
    for (const t of want) if (t.tWant === undefined) t.tWant = now;
    // v33 : tant que les tuiles de l'arrivée demandée ne sont pas prêtes, aucune autre tuile ne démarre
    if (anchorOpen()) want = want.filter(t => TL.anchor.tiles.includes(t));
    for (const t of want) {
      if (TL.inflight >= TL.conc) break;
      let u = tilesUsage();
      while (u.bytes + t.bytes > TL.maxBytes || u.tri + t.tri > TL.maxTri) {
        let v = null;
        for (const q of TL.tiles) if ((q.state === 'loading' || q.state === 'building' || q.state === 'ready') && q.d > t.d + 1 && (!v || q.d > v.d)) v = q;
        if (!v) break;
        tileUnload(v); u = tilesUsage();
      }
      if (u.bytes + t.bytes > TL.maxBytes || u.tri + t.tri > TL.maxTri) {
        if (t.d > 0 && u.n > 0) continue;   // plus de place : on attend qu'une tuile plus lointaine parte
        console.warn(tr('core.tile.budget', t.file));
      }
      tileStart(t);
    }
    tilesInfo();
  }
  // point dont la tuile est attendue : le téléport en attente, l'avatar, l'arrivée demandée
  function prioPoint() {
    if (TL.pending) return TL.pending.at;
    if (walking) return { x: W.pos.x, z: W.pos.z };
    return TL.anchor || null;
  }
  function releaseAnchor() { if (TL.anchor) { TL.anchor = null; TL.infoKey = ''; tilesInfo(); } }
  const markWait = (x, z) => { const n = performance.now(); if (n - TL.waitT > 600) TL.waitSince = n; TL.waitT = n; TL.waitAt = { x, z }; };
  function tilesPendingCheck() {
    const p = TL.pending;
    if (!p || TG.pending(p.at.x, p.at.z)) return;
    TL.pending = null;
    if (p.kind === 'walk') walkStart(p.opts); else teleportTo(p.pos, p.yaw);
    tilesInfo();
  }
  function tilesTick(now) {
    if (!TL.root) return;
    const t0 = performance.now();
    // v33 : la grille de la tuile qui contient l'avatar (ou l'arrivée / le téléport attendus) passe avant les autres, avec un budget par image plus généreux
    const foc = prioPoint();
    while (TL.gridQ.length) {
      let k = 0;
      if (foc) { const i = TL.gridQ.findIndex(q => inTile(q, foc.x, foc.z, TILE_M)); if (i > 0) k = i; }
      const t = TL.gridQ[k], prio = !!foc && inTile(t, foc.x, foc.z, TILE_M);
      if (performance.now() - t0 >= (prio ? GRID_MS_PRIO : GRID_MS)) break;
      const s0 = performance.now();
      if (t.qFirst) { t.qFirst = false; t.qWait = s0 - t.qAt; }
      let r;
      try { r = t.gen.next(); } catch (e) { TL.gridQ.splice(k, 1); tileUnload(t); tileFail(t, e); continue; }
      t.gridCpu += performance.now() - s0;
      if (r.done) { TL.gridQ.splice(k, 1); t.grid = r.value; t.gen = null; t.state = 'ready'; t.fails = 0; t.tWant = undefined; dirty = true; landKey = ''; tileReady(t); tilesPendingCheck(); tilesInfo(); }
    }
    if (TL.linkDirty) { TL.linkDirty = false; relinkZones(); }
    if (now - TL.lastUpd > 250) tilesUpdate(now);
    if (TL.waitT > 0 || TL.pending || TL.anchor) tilesInfo();
  }
  // vue d'ensemble : chargée avant les tuiles ; un échec n'est pas fatal (la région fonctionne alors comme en v30)
  async function loadOverview(ov, dir) {
    OV.state = 'loading';
    try {
      const buf = await TL.src.buf(dir + ov.file);
      const gltf = await loader.parseAsync(buf, '');
      const g = gltf.scene; g.name = 'overview';
      g.quaternion.copy(TL.root.quaternion);
      const byFile = new Map(TL.tiles.map(t => [t.file, t]));
      // v52 : le chemin ecrit dans le .overview.glb (extras.tile) est celui du decoupage ; apres un renommage des dossiers et de l'index il ne correspond plus :
      // repli sur le nom du fichier de la tuile (T_niveau_i_j.glb), unique dans une region (sinon pas de repli : la cellule reste visible)
      const baseOf = p => String(p || '').split('/').pop(), byBase = new Map(), dupBase = new Set();
      for (const t of TL.tiles) { const b = baseOf(t.file); if (byBase.has(b)) dupBase.add(b); else byBase.set(b, t); }
      let tri = 0, cells = 0;
      for (const c of g.children) {
        c.traverse(o => { if (o.isMesh) { o.matrixAutoUpdate = false; o.castShadow = o.receiveShadow = false; const gm = o.geometry; tri += gm.index ? gm.index.count / 3 : gm.attributes.position.count / 3; } });
        const tn = c.userData && c.userData.tile;
        const t = byFile.get(tn) || (dupBase.has(baseOf(tn)) ? undefined : byBase.get(baseOf(tn)));   // extras.tile : GLTFLoader retire « / », « . » et les espaces des noms de nœuds
        if (t) { t.ov = c; c.name = t.file; cells++; }
      }
      g.updateMatrixWorld(true);
      g.traverse(o => { if (o.isMesh) o.updateMatrix(); });
      scene.add(g);
      OV.root = g; OV.bytes = buf.byteLength; OV.tri = Math.round(tri); OV.cells = cells; OV.state = 'ready';
      for (const t of TL.tiles) ovSync(t);
      dirty = true;
    } catch (e) {
      OV.state = 'failed';
      console.warn(tr('core.ov.unavailable', ov.file, e && e.message ? e.message : e));
    }
  }
  // charge X.tiles.json puis les tuiles autour du point de départ ; rend la main quand les tuiles qui contiennent ce point sont prêtes
  // (ou en échec). opts : spawn (id d'arrivée du lien, sinon « default »), radius (?radius=)
  async function loadTiles(rel, opts) {
    opts = opts || {};
    if (opts.force) {
      if (TL.root) closeTiles();
      if (model) { if (walking) walkStop(); scene.remove(model); disposeObject(model); model = null; }   // un GLB unique ouvert avant
      TL.on = true;
    }   // le viewer ouvre une région en tuiles sans champ « tiles » dans une configuration
    if (!TL.on) throw new Error(tr('core.tile.off'));
    if (!safeRel(rel)) throw new Error(tr('core.tile.badpath', rel));
    // source des fichiers : adresses http relatives à la page (coquille, ou viewer avec ?tiles=), ou fichiers choisis dans un dossier (viewer)
    TL.src = opts.source || urlSource();
    const doc = await TL.src.json(rel);
    if (!doc || !Array.isArray(doc.tiles)) throw new Error(tr('core.tile.badformat', rel));
    const dir = rel.lastIndexOf('/') >= 0 ? rel.slice(0, rel.lastIndexOf('/') + 1) : '';
    TL.refs = !!doc.nodeRefs; TL.refsKnown = true; TL.refIndex.clear(); TL.linkSig = '';
    const num = (v, d, lo, hi) => { v = Number(v); return Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : d; };
    TL.radius = num(opts.radius, num(cfg.tileRadius, 150, 10, 5000), 10, 5000);
    TL.margin = num(cfg.tileMargin, 60, 0, 5000);
    TL.maxBytes = num(cfg.tileMaxMB !== undefined ? cfg.tileMaxMB : cfg.tileMaxMo, 200, 1, 1e5) * 1048576;
    TL.maxTri = num(cfg.tileMaxTriangles !== undefined ? cfg.tileMaxTriangles : cfg.tileMaxTri, 8e6, 1e3, 1e9);
    TL.conc = Math.round(num(cfg.tileConcurrency, 4, 1, 16));
    modelRot = rotDeg();
    const root = new THREE.Group(); root.name = 'tiles';
    if (modelRot) root.quaternion.setFromAxisAngle(UPV, modelRot * Math.PI / 180);
    root.updateMatrixWorld(true);
    const v = new THREE.Vector3(), ext = new THREE.Box3();
    for (const d of doc.tiles) {
      const ok = d && safeRel(d.file) && /\.glb$/i.test(d.file) && Array.isArray(d.min) && Array.isArray(d.max) && d.min.length === 3 && d.max.length === 3 && d.min.concat(d.max).every(Number.isFinite);
      if (!ok) { console.warn(tr('core.tile.ignored', rel), d && d.file); continue; }
      const b = new THREE.Box3();
      for (let k = 0; k < 8; k++) b.expandByPoint(v.set(k & 1 ? d.max[0] : d.min[0], k & 2 ? d.max[1] : d.min[1], k & 4 ? d.max[2] : d.min[2]).applyQuaternion(root.quaternion));
      ext.union(b);
      TL.tiles.push({ file: d.file, path: dir + d.file, bytes: Math.max(0, Number(d.bytes) || 0), tri: Math.max(0, Number(d.triangles) || 0),
        box: [b.min.x, b.min.z, b.max.x, b.max.z], ymin: b.min.y, ymax: b.max.y, state: 'idle', d: 0, fails: 0, retryAt: 0, ac: null, grp: null, grid: null, gen: null });
    }
    TL.root = root; model = root; TL.extent = ext; scene.add(root); TL.log = []; TL.anchor = null;
    if (!TL.refs) {   // tuiles sans références d'objets : les zones liées déjà posées sont retirées (avertissement), les libres restent
      const bad = zones.filter(z => z.mesh && z.type !== 'spawn');
      if (bad.length) { for (const z of bad) console.warn(tilesNoRefs(z)); zones = zones.filter(z => !bad.includes(z)); resolveLinks(); buildZones(); }
    }
    // v33 : arrivée demandée (lien #spawn=, #pos=, arrivée « default » à l'ouverture) : point de référence du chargeur jusqu'à la promenade ;
    // les tuiles qui la contiennent démarrent AVANT la vue d'ensemble et avant toute autre tuile
    let f = null;
    if (Array.isArray(opts.anchor) && opts.anchor.length >= 3 && opts.anchor.every(Number.isFinite)) f = { x: opts.anchor[0], z: opts.anchor[2] };
    else if (opts.spawn !== undefined) {
      const id = slug(opts.spawn), s = zones.find(z => z.type === 'spawn' && z.id === id) || zones.find(z => z.type === 'spawn' && z.id === 'default');
      if (s) f = { x: s.x, z: s.z };
    }
    if (f) {
      const now0 = performance.now();
      TL.anchor = { x: f.x, z: f.z, t0: now0, tx: controls.target.x, tz: controls.target.z, tiles: tilesAt(f.x, f.z) };
      tilesUpdate(now0);
    }
    const ovd = doc.overview;
    if (ovd && typeof ovd === 'object' && safeRel(ovd.file) && /\.glb$/i.test(ovd.file)) await loadOverview(ovd, dir);
    else if (ovd) console.warn(tr('core.ov.ignored'), ovd && ovd.file);
    const tanH = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    if (OV.state === 'ready' && !ext.isEmpty()) {
      // la vue d'ensemble montre toute la région : la caméra se cadre sur l'étendue entière (brouillard et plan lointain suivent)
      fit = Math.max(ext.max.x - ext.min.x, ext.max.z - ext.min.z, ext.max.y - ext.min.y, 200) / 2 / tanH * 1.35;
      const D = fit * Math.max(1, Number(cfg.zoom) || 1);
      controls.maxDistance = Math.max(controls.maxDistance, D * 1.5);
      scene.fog.near = Math.max(scene.fog.near, D * 1.1); scene.fog.far = Math.max(scene.fog.far, D * 3);
      camera.far = Math.max(camera.far, scene.fog.far + D); camera.updateProjectionMatrix();
    } else {
      // pas de vue d'ensemble : la caméra se cadre sur le rayon de chargement, pas sur toute la région
      fit = Math.max(2 * TL.radius, 200) / 2 / tanH * 1.35;
    }
    if (!ext.isEmpty()) { seaCx = (ext.min.x + ext.max.x) / 2; seaCz = (ext.min.z + ext.max.z) / 2; if (sea) sea.position.set(seaCx, cfg.seaY, seaCz); }
    frame(cfg.camDir, opts.target || cfg.target, cfg.zoom);
    if (TL.anchor) { TL.anchor.tx = controls.target.x; TL.anchor.tz = controls.target.z; }
    if (!f) f = { x: controls.target.x, z: controls.target.z };
    const now = performance.now();
    if (!TL.anchor) { TL.forced = f; TL.forcedUntil = now + 4000; }   // le temps que la coquille démarre la promenade (sans arrivée demandée)
    tilesUpdate(now);
    // attend les tuiles qui contiennent le point de départ (sinon la plus proche) : prêtes ou en échec, au plus opts.waitMs (15 s par défaut) ;
    // ensuite la page continue : la promenade démarre dès que la tuile est prête (TL.pending), « Chargement du sol… » reste affiché
    const waitSet = TL.anchor ? TL.anchor.tiles : tilesAt(f.x, f.z);
    const t1 = performance.now(), maxMs = Number.isFinite(opts.waitMs) ? opts.waitMs : 15000;
    await new Promise(res => { const chk = () => (waitSet.every(tileDone) || performance.now() - t1 > maxMs) ? res() : setTimeout(chk, 100); chk(); });
    dirty = true;
    return { tiles: TL.tiles.length, extent: ext.isEmpty() ? null : ext.min.toArray().concat(ext.max.toArray()), ready: waitSet.every(t => t.state === 'ready'), waited: Math.round(performance.now() - t1) };
  }
  function tilesState() {
    const names = t => TL.tiles.filter(q => t.includes(q.state)).map(q => q.file);
    return Object.assign(tilesStatus(), { on: TL.on, radius: TL.radius, margin: TL.margin, maxBytes: TL.maxBytes, maxTri: TL.maxTri, conc: TL.conc,
      overview: { state: OV.state, bytes: OV.bytes, tri: OV.tri, cells: OV.cells, visible: OV.root ? OV.root.children.filter(c => c.visible).map(c => c.name) : [], hidden: OV.root ? OV.root.children.filter(c => !c.visible).map(c => c.name) : [] },
      ready: names(['ready']), loadingFiles: names(['loading', 'building']), failedFiles: names(['failed']), groups: TL.root ? TL.root.children.map(c => c.name) : [], inflight: TL.inflight, gridQueue: TL.gridQ.length,
      anchor: TL.anchor ? { x: TL.anchor.x, z: TL.anchor.z, files: TL.anchor.tiles.map(t => t.file) } : null, log: TL.log.slice() });
  }

  function setCfg(p) {
    Object.assign(cfg, p);
    if ('zoneMarker' in p) cfg.zoneMarker = zmNorm(cfg.zoneMarker);
    if ('skyColor' in p) { scene.background.set(cfg.skyColor); scene.fog.color.set(cfg.skyColor); hemi.color.set(cfg.skyColor); }
    if ('retina' in p || 'pixelScale' in p) resize();
    // v42 : rayon des tuiles et vue d'ensemble seule, pris en compte au prochain tour de choix des tuiles (250 ms au plus)
    if ('tileRadius' in p && TL.on && Number(cfg.tileRadius) > 0) { TL.radius = Math.min(5000, Math.max(10, Number(cfg.tileRadius))); TL.lastUpd = 0; }
    if ('ovOnly' in p && TL.on) TL.lastUpd = 0;
    if ('rotate' in p) applyRotation();
    if ('sea' in p || 'anim' in p || 'seaSegments' in p) buildSea();
    else if (seaMat) {
      if ('seaColor' in p) { if (seaMat.uniforms) seaMat.uniforms.uColor.value.set(cfg.seaColor); else seaMat.color.set(cfg.seaColor); }
      if (seaMat.uniforms) {
        seaMat.uniforms.uAmp.value = cfg.wave;
        seaMat.uniforms.uHoleRadius.value = cfg.hole;
        seaMat.uniforms.uHoleFade.value = cfg.holeFade;
        seaMat.uniforms.uHoleCenter.value.set(cfg.holeX, -cfg.holeZ);
      }
    }
    if (sea) sea.position.set(seaCx, cfg.seaY, seaCz);
    if ('zoneMarker' in p || 'showSpawns' in p) buildZones();
    if ('foliageCutout' in p) foliageMats.forEach(m => { m.alphaTest = cfg.foliageCutout; m.needsUpdate = true; });
    dirty = true;
    if (onCfg) onCfg(cfg);
  }

  function getCameraState() {
    const off = camera.position.clone().sub(controls.target);
    const dist = off.length();
    return { camDir: off.normalize().toArray(), target: controls.target.toArray(), zoom: dist / fit };
  }

  function setZoom(z) {
    const off = camera.position.clone().sub(controls.target);
    if (off.lengthSq() < 1e-8) off.set(0, 0.25, 1);
    camera.position.copy(controls.target).addScaledVector(off.normalize(), fit * z);
    controls.update();
    dirty = true;
  }

  // ---- promenade à hauteur d'avatar
  const dom = renderer.domElement;
  const STEP_UP = 0.6;
  // v33 : vol (touche Début : E monte, C descend, pas de gravité, murs solides, jamais sous le sol) et trois vues (V) :
  // 'fps' subjective, 'tps' à la troisième personne (la caméra tourne autour de l'avatar), 'free' caméra libre (l'avatar reste sur place)
  const VIEWS = ['fps', 'tps', 'free'], VIEW_NAMES = { fps: tr('core.view.fps'), tps: tr('core.view.tps'), free: tr('core.view.free') };
  let selfAv = null, selfKey = '';
  function updateSelf() {
    const show = walking && W.view !== 'fps';
    if (!show) { if (selfAv && selfAv.visible) { selfAv.visible = false; dirty = true; } return; }
    const col = P.myColor !== null ? P.myColor : (P.serverColor !== null ? P.serverColor : 0x3366cc), key = P.name + '|' + col;
    if (!selfAv || selfKey !== key) { if (selfAv) disposeAvatar(selfAv); selfAv = makeAvatar(P.name || 'Moi', col); scene.add(selfAv); selfKey = key; }
    selfAv.visible = true; selfAv.position.set(W.pos.x, W.pos.y, W.pos.z); selfAv.rotation.y = W.yaw; dirty = true;
  }
  // sol sous un point de caméra : la surface la plus haute à moins de 1 m au-dessus, sinon (point enfoui sous le relief) la plus haute à moins de 12 m au-dessus
  function floorAt(G, x, z, y) { let g = G.ground(x, z, y + 1); if (g === null) g = G.ground(x, z, y + 12); return g; }
  function placeCamera(G, hasGround) {
    const eyeY = W.pos.y + cfg.eyeHeight;
    if (W.view === 'free') { camera.position.copy(W.cam); camera.rotation.set(W.cpitch, W.cyaw, 0); return; }
    if (W.view === 'tps') {
      const cp = Math.cos(W.tpitch), sp = Math.sin(W.tpitch), sy = Math.sin(W.tyaw), cy = Math.cos(W.tyaw);
      const fx = -sy * cp, fy = sp, fz = -cy * cp;   // direction du regard de la caméra (v35 : indépendante de l'orientation de l'avatar)
      let D = W.tdist;
      if (hasGround) {   // un mur entre l'avatar et la caméra : la caméra se rapproche
        const hl = Math.hypot(fx, fz) || 1, hit = G.wall(W.pos.x, eyeY, W.pos.z, -fx / hl, -fz / hl, D * Math.max(cp, 0.3) + 0.3);
        if (hit) D = Math.max(0.5, (hit.t - 0.3) / Math.max(cp, 0.3));
      }
      const cx = W.pos.x - fx * D, cz = W.pos.z - fz * D; let cy2 = eyeY - fy * D;
      if (hasGround) { const g = floorAt(G, cx, cz, cy2); if (g !== null && cy2 < g + 0.3) cy2 = g + 0.3; }   // la caméra ne traverse pas le sol
      camera.position.set(cx, cy2, cz); camera.lookAt(W.pos.x, eyeY, W.pos.z);
      return;
    }
    camera.position.set(W.pos.x, eyeY, W.pos.z);
    camera.rotation.set(W.pitch, W.yaw, 0);
  }
  function walkStep(dt) {
    const k = W.keys, free = W.view === 'free', tps = W.view === 'tps';
    for (const c of W.run) if (!k.has(c)) W.run.delete(c);   // v35 : course par double appui (W, S, ↑, ↓) : tant que la touche reste enfoncée
    const run = k.has('ShiftLeft') || k.has('ShiftRight') || W.run.size > 0 || !!W.runLatch;   // v46 : bouton « Courir » des flèches à l'écran (un clic l'allume, un clic l'éteint)
    if (run !== !!W.runOn) { W.runOn = run; if (onView) onView(); }   // v37 : la ligne « Mode » de l'état affiche la course
    const turn = (k.has('ArrowLeft') ? 1 : 0) - (k.has('ArrowRight') ? 1 : 0);
    if (turn) { if (free) W.cyaw += 1.8 * dt * turn; else if (tps) W.tyaw += 1.8 * dt * turn; else W.yaw += 1.8 * dt * turn; }
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const s = (k.has('KeyD') ? 1 : 0) - (k.has('KeyA') ? 1 : 0);
    const up = (k.has('PageUp') || (W.fly && k.has('Space')) ? 1 : 0) - (k.has('KeyC') || k.has('PageDown') ? 1 : 0);   // v36 : monter = Page Haut ou Espace maintenu (en vol) ; E ne sert plus qu'aux zones
    const G = W.grid, hasGround = G && (G.count > 0 || G.tiled);
    let speed = cfg.walkSpeed * (run ? 2.2 : 1);
    if (free) {
      // v35 : la vitesse suit la distance caméra-avatar (au moins la marche, 0,5 x la distance par seconde, 60 m/s au plus) ; Maj la multiplie par 3
      const dd = Math.hypot(W.cam.x - W.pos.x, W.cam.y - (W.pos.y + cfg.eyeHeight), W.cam.z - W.pos.z);
      speed = Math.min(60, Math.max(cfg.walkSpeed, 0.5 * dd)) * ((k.has('ShiftLeft') || k.has('ShiftRight')) ? 3 : 1);
      // caméra libre : les touches déplacent la caméra (dans le sens du regard), l'avatar reste sur place
      const sy = Math.sin(W.cyaw), cy = Math.cos(W.cyaw), cp = Math.cos(W.cpitch), sp = Math.sin(W.cpitch);
      let mx = -sy * cp * f + cy * s, my = sp * f + up, mz = -cy * cp * f - sy * s;
      const len = Math.hypot(mx, my, mz);
      if (len > 0 && dt > 0) {
        const d = speed * dt / len, nx = W.cam.x + mx * d, nz = W.cam.z + mz * d;
        if (hasGround && G.tiled && G.pending(nx, nz)) markWait(nx, nz);
        else { W.cam.x = nx; W.cam.z = nz; W.cam.y += my * d; }
      }
      if (hasGround) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }   // jamais sous le sol
    }
    const mf = free ? 0 : f, ms = free ? 0 : s;
    const my0 = tps ? W.tyaw : W.yaw, sy = Math.sin(my0), cy = Math.cos(my0);   // v35 : à la troisième personne la marche suit la caméra
    let mx = -sy * mf + cy * ms, mz = -cy * mf - sy * ms;
    const len = Math.hypot(mx, mz);
    if (len > 0 && dt > 0) {
      mx /= len; mz /= len;
      if (tps) { let d = Math.atan2(-mx, -mz) - W.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); W.yaw += d * (1 - Math.exp(-dt * 8)); }   // l'avatar se tourne vers sa direction de déplacement (lissé)
      const dist = speed * dt;
      let dx = mx * dist, dz = mz * dist;
      if (hasGround) {
        const hit = G.wall(W.pos.x, W.pos.y + 0.9, W.pos.z, mx, mz, dist + 0.35);
        if (hit) {
          let nx = hit.nx, nz = hit.nz; const nl = Math.hypot(nx, nz) || 1; nx /= nl; nz /= nl;
          if (nx * mx + nz * mz > 0) { nx = -nx; nz = -nz; }
          const d = dx * nx + dz * nz; dx -= d * nx; dz -= d * nz;
        }
        // mode tuiles : jamais d'avancée vers une zone dont la tuile n'est pas prête (indicateur « Chargement du sol… »)
        if (G.tiled && G.pending(W.pos.x + dx, W.pos.z + dz)) markWait(W.pos.x + dx, W.pos.z + dz);
        else if (W.fly || G.ground(W.pos.x + dx, W.pos.z + dz, W.pos.y + STEP_UP) !== null) { W.pos.x += dx; W.pos.z += dz; }
      } else { W.pos.x += dx; W.pos.z += dz; }
    }
    // v36 : Page Haut maintenu au sol plus de 0,4 s : décollage (vol + montée) ; un appui bref a déjà fait sauter l'avatar
    if (k.has('PageUp') && !W.fly && !free && cfg.fly !== false) { W.upT += dt; if (W.upT > 0.4) startFly(); } else W.upT = 0;
    if (W.fly) {
      // en vol : pas de gravité ; E monte, C descend ; jamais sous le sol des tuiles chargées (tuile dessous pas prête : on ne descend pas)
      W.vy = 0; W.grounded = false; W.jumpReq = false;
      const gF = hasGround ? G.ground(W.pos.x, W.pos.z, W.pos.y + STEP_UP) : null;
      if (gF !== null) W.flyFloor = gF;
      let ny = W.pos.y + (free ? 0 : up) * speed * dt;
      if (hasGround && G.tiled && G.pending(W.pos.x, W.pos.z)) { if (ny < W.pos.y) { ny = W.pos.y; markWait(W.pos.x, W.pos.z); } }
      else if (hasGround) {
        const fl = gF !== null ? gF : W.flyFloor;
        if (fl !== undefined && ny < fl) ny = fl;
        // v34 : en descendant jusqu'au sol, l'avatar atterrit tout seul (le vol s'arrête ; jamais sous le sol)
        if (fl !== undefined && up < 0 && !free && ny <= fl + 1e-3) { W.pos.y = fl; W.fly = false; W.vy = 0; W.grounded = true; W.keys.delete('KeyC'); W.keys.delete('PageDown'); if (onFly) onFly(false); dirty = true; ny = fl; }
      }
      W.pos.y = ny;
    } else {
      if ((W.jumpReq || k.has('Space')) && W.grounded && !free) { W.vy = 5.5; W.grounded = false; W.pos.y += 0.02; }
      W.jumpReq = false;
      const g = hasGround ? G.ground(W.pos.x, W.pos.z, W.pos.y + STEP_UP) : null;
      if (W.grounded) {
        if (g !== null) {
          if (W.pos.y - g > 0.6) W.grounded = false;
          else W.pos.y += (g - W.pos.y) * Math.min(1, dt * 18);
        }
      }
      if (!W.grounded && !(G && G.tiled && G.pending(W.pos.x, W.pos.z))) {
        W.vy -= 15 * dt; W.pos.y += W.vy * dt;
        if (g !== null && W.pos.y <= g) { W.pos.y = g; W.vy = 0; W.grounded = true; }
        if (W.pos.y < W.spawn.y - 400) { W.pos.copy(W.spawn); W.vy = 0; W.grounded = true; }
      }
    }
    placeCamera(G, hasGround);
    updateSelf();
    if (dt > 0) { zoneTick(); if (zoneLabs.length) zoneLabelTick(); }
  }
  function setView(v) {
    if (!walking || !VIEWS.includes(v) || v === W.view) return W.view;
    const fromTps = W.view === 'tps';
    if (v === 'free') { W.cam.copy(camera.position); W.cyaw = fromTps ? W.tyaw : W.yaw; W.cpitch = fromTps ? W.tpitch : W.pitch; }
    else if (W.view === 'free') W.keys.clear();
    if (v === 'tps') { W.tyaw = W.yaw; W.tpitch = fromTps ? W.tpitch : W.pitch; }   // v35 : la caméra repart de la direction du regard
    else if (fromTps) { W.yaw = W.tyaw; W.pitch = W.tpitch; }   // retour à la vue subjective : le regard garde la direction de la caméra
    W.view = v; walkStep(0); dirty = true;
    if (onView) onView(v, VIEW_NAMES[v]);
    return v;
  }
  const cycleView = () => setView(VIEWS[(VIEWS.indexOf(W.view) + 1) % VIEWS.length]);
  function startFly() {   // décollage par touche maintenue : les touches tenues restent actives (la montée continue)
    if (!walking || W.fly || cfg.fly === false) return false;
    W.fly = true; W.vy = 0; W.grounded = false; W.upT = 0;
    if (onFly) onFly(true);
    dirty = true;
    return true;
  }
  // v35 : touche M / Fin / Alt+clic : la caméra revient derrière l'avatar
  function setTpsDist(d) { W.tdist = Math.max(1, Math.min(30, d)); try { localStorage.setItem('glb2html_tpsDist', String(W.tdist)); } catch (_) {} }
  function recenterCam() {
    if (!walking) return false;
    W.tyaw = W.yaw; W.tpitch = 0.12;
    if (W.view === 'tps') setTpsDist(4);
    else if (W.view === 'free') {   // caméra libre : derrière l'avatar, à la distance par défaut, le regard sur lui
      const D = 4, cp = Math.cos(W.tpitch), sp = Math.sin(W.tpitch), eyeY = W.pos.y + cfg.eyeHeight;
      W.cam.set(W.pos.x + Math.sin(W.yaw) * cp * D, eyeY - sp * D, W.pos.z + Math.cos(W.yaw) * cp * D); W.cyaw = W.yaw; W.cpitch = W.tpitch;
      const G = W.grid; if (G && (G.count > 0 || G.tiled)) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }
    }
    walkStep(0); dirty = true; return true;
  }
  function toggleFly() {
    if (!walking || cfg.fly === false) return false;
    W.fly = !W.fly; W.vy = 0; W.keys.clear(); W.upT = 0;
    if (W.fly) W.grounded = false; else W.grounded = false;   // à l'atterrissage la gravité ramène l'avatar sur le sol des tuiles chargées
    if (onFly) onFly(W.fly);
    dirty = true;
    return W.fly;
  }
  // v36 : arrivée occupée. À chaque pose de l'avatar sur un point (ouverture, arrivée par défaut, R, portail, « Aller à », #pos), si un autre visiteur EN PROMENADE
  // est à moins de 1 m en horizontal (2 m en vertical), le NOUVEL ARRIVANT passe au point libre le plus proche : anneaux de 1,2, 2,4 puis 3,6 m (12, 16, 24 candidats),
  // sol à moins de 1 m d'écart de hauteur, aucun mur entre le point demandé et le candidat, aucun visiteur à moins de 1 m. Sans place libre : pose à l'endroit demandé.
  // Présence pas encore connectée (liste des visiteurs inconnue) : le contrôle est refait à la réception de la liste, seulement si l'avatar n'a pas bougé de plus de 0,3 m.
  const DODGE = { pending: null };
  function peerNear(x, y, z, rh, rv) {
    for (const q of P.peers.values()) if (q.g.visible && Math.hypot(q.tx - x, q.tz - z) < rh && Math.abs(q.ty - y) < rv) return true;
    return false;
  }
  // v37 : le point libre le plus proche de l'OCCUPANT (anneaux de 1,5 puis 2,0 puis 3,0 m autour de lui, 16 candidats), le plus proche du point demandé dans l'anneau ;
  // l'arrivant est ensuite tourné vers l'occupant le plus proche (avant = (-sin yaw, -cos yaw), comme getWalk().yaw)
  function dodgeSpot(x, y, z) {
    if (!peerNear(x, y, z, 1, 2)) return null;
    const G = W.grid; if (!G) return null;
    let occ = null, od = 1e9;
    for (const q of P.peers.values()) { if (!q.g.visible || Math.abs(q.ty - y) >= 2) continue; const d = Math.hypot(q.tx - x, q.tz - z); if (d < 1 && d < od) { od = d; occ = q; } }
    if (!occ) return null;
    const ox = occ.tx, oz = occ.tz, oy = occ.ty;
    for (const r of [1.5, 2.0, 3.0]) {
      const n = 16, found = [];
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2, cx = ox + Math.cos(a) * r, cz = oz + Math.sin(a) * r;
        if (G.tiled && G.pending(cx, cz)) continue;
        const g = G.ground(cx, cz, y + 1);
        if (g === null || Math.abs(g - y) > 1) continue;
        if (G.wall(ox, oy + 0.9, oz, Math.cos(a), Math.sin(a), r + 0.3)) continue;
        if (peerNear(cx, g, cz, 1, 2)) continue;
        found.push({ x: cx, y: g, z: cz, r, dp: Math.hypot(cx - x, cz - z), dy: Math.abs(g - y) });
      }
      if (found.length) { found.sort((p, q) => (p.dp - q.dp) || (p.dy - q.dy)); return found[0]; }
    }
    return null;
  }
  function dodgeNow() {
    const x0 = W.pos.x, z0 = W.pos.z, s = dodgeSpot(x0, W.pos.y, z0);
    if (!s) return false;
    W.pos.set(s.x, s.y, s.z); W.spawn.copy(W.pos);
    let near = null, nd = 4;
    for (const q of P.peers.values()) { if (!q.g.visible) continue; const d = Math.hypot(q.tx - s.x, q.tz - s.z); if (d < nd) { nd = d; near = q; } }
    if (near) { W.yaw = W.tyaw = Math.atan2(-(near.tx - s.x), -(near.tz - s.z)); W.pitch = 0; }
    console.log(tr('core.dodge.log', (Math.round(Math.hypot(s.x - x0, s.z - z0) * 10) / 10).toFixed(1), s.r.toFixed(1)));
    return true;
  }
  function dodgeApply() {
    DODGE.pending = null;
    if (!cfg.presenceUrl) return;
    if (P.ws && P.ws.readyState === 1 && P.id) dodgeNow();
    else DODGE.pending = { x: W.pos.x, y: W.pos.y, z: W.pos.z, t: performance.now() };
  }
  function dodgeWelcome() {
    const d = DODGE.pending; DODGE.pending = null;
    if (d && walking && W.grid && performance.now() - d.t < 20000 && Math.hypot(W.pos.x - d.x, W.pos.y - d.y, W.pos.z - d.z) <= 0.3) { dodgeNow(); dirty = true; }
  }
  function walkStart(opts) {
    if (!model || walking) return walking;
    // v33 : F sans point demandé démarre à l'arrivée « default » tant que la cible n'a pas bougé (sinon à la cible, comme avant)
    if (!opts && home && home.forF && Math.hypot(controls.target.x - home.pos[0], controls.target.z - home.pos[2]) < 0.05) opts = { pos: home.pos, yaw: home.yaw };
    if (TL.on) {
      // la promenade attend que la tuile sous l'avatar soit prête (F de nouveau : annuler)
      const at = (opts && opts.pos) ? { x: opts.pos[0], z: opts.pos[2] } : { x: controls.target.x, z: controls.target.z };
      if (TG.pending(at.x, at.z)) { TL.pending = { kind: 'walk', opts, at, t0: TL.pending ? TL.pending.t0 : (TL.anchor ? TL.anchor.t0 : performance.now()) }; markWait(at.x, at.z); tilesUpdate(TL.waitT); return false; }
      TL.pending = null; TL.forced = null; releaseAnchor();
    }
    W.grid = TL.on ? TG : buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore));
    W.saved = { pos: camera.position.clone(), target: controls.target.clone(), fov: camera.fov };
    const t = (opts && opts.pos) ? new THREE.Vector3().fromArray(opts.pos) : controls.target, fx = t.x - camera.position.x, fz = t.z - camera.position.z;
    W.yaw = (opts && Number.isFinite(opts.yaw)) ? opts.yaw : (Math.hypot(fx, fz) > 1e-3 ? Math.atan2(-fx, -fz) : 0);
    W.pitch = 0; W.tyaw = W.yaw; W.tpitch = 0; W.run.clear(); W.upT = 0; W.runOn = false;
    let g = W.grid.ground(t.x, t.z, t.y + 2);
    if (g === null) g = W.grid.ground(t.x, t.z, 1e6);
    W.pos.set(t.x, g === null ? t.y : g, t.z); W.spawn.copy(W.pos);
    dodgeApply();
    W.vy = 0; W.grounded = true; W.keys.clear(); W.drag = false; W.fly = false; W.flyFloor = undefined; W.view = 'fps'; W.mouseFree = false;
    controls.enabled = false;
    camera.fov = 70; camera.updateProjectionMatrix();
    camera.rotation.order = 'YXZ';
    walking = true;
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
    zoneInside.clear(); nearZone = null;
    for (const z of zones) if (z.type === 'portal' && z.trigger !== 'click' && !zoneOff(z) && zoneDist(z).d <= z.radius) zoneInside.add(z.id);
    walkStep(0); dirty = true;
    presenceEnter();
    if (onWalk) onWalk(true);
    return true;
  }
  // P (et le bouton) : entre ou sort de la promenade
  function toggleWalk() {
    if (TL.pending) { TL.pending = null; tilesInfo(); return false; }
    return walking ? walkStop() : walkStart();
  }
  // v36 : F (comme P) entre en promenade et en sort, en vue globale comme en promenade, y compris pendant l'attente d'une tuile (annule) ; le vol se bascule avec Début ou le bouton
  function pressF() { return toggleWalk(); }
  function walkStop() {
    if (!walking) return;
    walking = false; W.keys.clear(); W.drag = false; W.fly = false; W.view = 'fps'; W.runLatch = false; updateSelf();
    if (document.pointerLockElement === dom && document.exitPointerLock) document.exitPointerLock();
    camera.rotation.order = 'XYZ';
    camera.fov = W.saved.fov; camera.updateProjectionMatrix();
    // v31 : la cible de la vue globale (cercle d'atterrissage) passe au sol sous l'avatar ; la caméra garde le décalage (distance et direction)
    // qu'elle avait avant l'entrée en promenade. En mode tuiles le chargeur suit cette cible : les tuiles autour de l'avatar restent.
    const off = W.saved.pos.clone().sub(W.saved.target);
    let gy = W.grid ? W.grid.ground(W.pos.x, W.pos.z, W.pos.y + 2) : null;
    if (gy === null) gy = W.pos.y;
    controls.target.set(W.pos.x, gy, W.pos.z);
    camera.position.copy(controls.target).add(off);
    controls.enabled = true; controls.update();
    landKey = '';
    W.grid = null; dirty = true;
    zoneInside.clear(); if (nearZone) { nearZone = null; if (onNear) onNear(null); }
    DODGE.pending = null;
    presenceLeave();
    if (zoneLabs.length) zoneLabelTick();
    if (onWalk) onWalk(false);
  }

  // téléportation dans la même région (portail interne) : pose l'avatar en pos/yaw sans quitter la promenade
  function teleportTo(pos, yaw) {
    if (!model) return false;
    if (!walking) return walkStart({ pos, yaw });
    const x = pos[0], y = pos[1], z = pos[2];
    if (TL.on && TG.pending(x, z)) { TL.pending = { kind: 'tp', pos, yaw, at: { x, z }, t0: TL.pending ? TL.pending.t0 : performance.now() }; markWait(x, z); tilesUpdate(TL.waitT); return true; }
    let g = W.grid.ground(x, z, y + 2);
    if (g === null) g = W.grid.ground(x, z, 1e6);
    W.pos.set(x, g === null ? y : g, z); W.spawn.copy(W.pos);
    dodgeApply();
    if (Number.isFinite(yaw)) { W.yaw = yaw; W.tyaw = yaw; }
    W.pitch = 0; W.vy = 0; W.grounded = true;
    zoneInside.clear(); nearZone = null; if (onNear) onNear(null);
    for (const q of zones) if (q.type === 'portal' && q.trigger !== 'click' && !zoneOff(q) && zoneDist(q).d <= q.radius) zoneInside.add(q.id);
    walkStep(0); dirty = true;
    return true;
  }
  // v46 : vue globale pas à pas (flèches à l'écran) : fwd, side, dir dans [-1, 1], dt en secondes. Le pas suit la distance de la caméra à la cible
  // (60 % de cette distance par seconde, 2 m au moins) ; tourner : 1,2 rad/s autour de la cible (gauche = sens inverse des aiguilles vu d'en haut) ;
  // rapprocher / éloigner : facteur e^(1,2 dt), dans les bornes d'OrbitControls. Sans effet en promenade.
  function globalMove(fwd, side, dt) {
    if (walking || !Number.isFinite(dt) || dt <= 0) return false;
    const off = camera.position.clone().sub(controls.target), d = off.length();
    const f = new THREE.Vector3(-off.x, 0, -off.z); if (f.lengthSq() < 1e-9) f.set(0, 0, -1); f.normalize();
    const r = new THREE.Vector3(-f.z, 0, f.x), step = Math.max(2, d) * 0.6 * Math.min(dt, 0.25);
    const m = f.multiplyScalar((fwd || 0) * step).add(r.multiplyScalar((side || 0) * step));
    camera.position.add(m); controls.target.add(m); controls.update(); landKey = ''; dirty = true;
    return true;
  }
  function globalTurn(dir, dt) {
    if (walking || !Number.isFinite(dt) || dt <= 0) return false;
    const off = camera.position.clone().sub(controls.target).applyAxisAngle(new THREE.Vector3(0, 1, 0), (dir || 0) * 1.2 * Math.min(dt, 0.25));
    camera.position.copy(controls.target).add(off); controls.update(); dirty = true;
    return true;
  }
  function globalZoom(dir, dt) {
    if (walking || !Number.isFinite(dt) || dt <= 0) return false;
    const off = camera.position.clone().sub(controls.target), d = off.length() || 1;
    const nd = Math.max(controls.minDistance, Math.min(controls.maxDistance, d * Math.exp((dir || 0) * 1.2 * Math.min(dt, 0.25))));
    camera.position.copy(controls.target).add(off.multiplyScalar(nd / d)); controls.update(); dirty = true;
    return true;
  }
  // v33 : aller à un point (champ « Aller à », retour à l'arrivée) : en promenade, téléportation (attend la tuile, « Chargement du sol… ») ;
  // en vue globale, la cible se déplace (la caméra la suit, avec le même décalage) et le chargeur de tuiles aussi
  function goTo(pos, yaw) {
    if (!model || !Array.isArray(pos) || pos.length < 3 || !pos.every(Number.isFinite)) return false;
    if (walking) return teleportTo(pos.slice(0, 3), yaw);
    const d = new THREE.Vector3().fromArray(pos).sub(controls.target);
    camera.position.add(d); controls.target.add(d); controls.update();
    landKey = ''; dirty = true;
    if (TL.on) { TL.forced = { x: pos[0], z: pos[2] }; TL.forcedUntil = performance.now() + 15000; tilesUpdate(performance.now()); }
    return true;
  }
  const returnHome = () => (home ? goTo(home.pos, home.yaw) : false);
  // v34 : souris libre (le pointeur vient d'être libéré en promenade : Échap, perte de focus). Après la v52, un clic, un double-clic ou un clic sur une zone
  // ne capturent JAMAIS la souris : la capture est volontaire (touche G, bouton « Capturer la souris »). L'état « libre » ne sert plus qu'à l'afficher.
  function grabMouse() {
    if (!walking) return false;
    W.mouseFree = false;
    try { const p = dom.requestPointerLock(); if (p && p.catch) p.catch(() => {}); } catch (_) {}
    if (onMouse) onMouse(mouseState());
    return true;
  }
  // après la v52 : la touche G BASCULE (capture si la souris est libre, libère si elle est capturée) ; le bouton « Capturer la souris » ne fait que capturer
  // (un pointeur verrouillé ne peut rien cliquer). exitPointerLock déclenche pointerlockchange : l'état « libre » et l'interface suivent.
  function toggleMouse() {
    if (!walking) return false;
    if (document.pointerLockElement === dom) { try { document.exitPointerLock(); } catch (_) {} return true; }
    return grabMouse();
  }
  const mouseState = () => (document.pointerLockElement === dom ? 'captured' : (W.mouseFree ? 'free' : 'idle'));
  document.addEventListener('pointerlockchange', () => {
    if (!walking) return;   // sortie de promenade : walkStop libère le pointeur lui-même
    W.mouseFree = document.pointerLockElement !== dom;
    if (onMouse) onMouse(mouseState());
  });
  const typing = e => { const n = e.target && e.target.tagName; return n === 'INPUT' || n === 'TEXTAREA' || n === 'SELECT'; };
  const MOVE_KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyC', 'PageUp', 'PageDown', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'ShiftLeft', 'ShiftRight']);
  const RUN_TAP = new Set(['KeyW', 'KeyS', 'ArrowUp', 'ArrowDown']);
  window.addEventListener('keydown', e => {
    if (!walking || typing(e)) return;
    if (e.code === 'AltLeft' || e.code === 'AltRight') { e.preventDefault(); return; }   // Alt seul n'ouvre pas le menu du navigateur
    if (e.repeat) return;
    const mod = e.ctrlKey || e.metaKey || e.altKey;
    if (e.code === 'Home' && cfg.fly !== false) { toggleFly(); e.preventDefault(); }
    else if (e.code === 'End' && !mod) { recenterCam(); e.preventDefault(); }
    else if (e.code === 'KeyV' && !mod) cycleView();
    else if (keyChar(e) === 'm' && !mod) setView(W.view === 'tps' ? 'fps' : 'tps');   // v36 : reconnue par la lettre imprimée (« m »), pas par la place de la touche ; v35 : M bascule vue subjective / troisième personne (Ctrl+M : carte des mondes)
    else if (e.code === 'KeyG' && !mod) toggleMouse();
  });
  window.addEventListener('keydown', e => { if (!walking || typing(e) || !MOVE_KEYS.has(e.code) || e.ctrlKey || e.metaKey || e.altKey) return;   // v34 : Ctrl+C copie (le texte de l'aide est sélectionnable)
    const c = e.code;
    if (c === 'Space' && !W.fly) W.jumpReq = true;
    if (!e.repeat) {
      const now = performance.now();
      if (RUN_TAP.has(c)) { if (W.tap[c] !== undefined && now - W.tap[c] < 300) W.run.add(c); W.tap[c] = now; }   // v35 : double appui rapide = course
      if (c === 'PageUp' && !W.fly && W.view !== 'free') W.jumpReq = true;   // appui bref au sol = saut (maintenu plus de 0,4 s : décollage)
    }
    W.keys.add(c); e.preventDefault(); });
  window.addEventListener('keyup', e => { W.keys.delete(e.code); W.run.delete(e.code); if (walking && (e.code === 'AltLeft' || e.code === 'AltRight')) e.preventDefault(); });
  window.addEventListener('blur', () => { W.keys.clear(); W.run.clear(); });
  dom.addEventListener('mousedown', () => { if (walking) { W.drag = true; W.moved = false; } });
  window.addEventListener('mouseup', () => { W.drag = false; });
  window.addEventListener('mousemove', e => {
    if (!walking || !(W.drag || document.pointerLockElement === dom)) return;
    if (W.drag && (e.movementX || e.movementY)) W.moved = true;
    if (W.view === 'free' && e.altKey) {   // v35 : Alt + glisser : la caméra orbite autour de l'avatar en gardant sa distance, le regard sur lui
      const ex = W.pos.x, ey = W.pos.y + cfg.eyeHeight, ez = W.pos.z;
      let ox = W.cam.x - ex, oy = W.cam.y - ey, oz = W.cam.z - ez; const d = Math.hypot(ox, oy, oz) || 1;
      let az = Math.atan2(ox, oz) - (e.movementX || 0) * 0.0022, el = Math.max(-1.45, Math.min(1.45, Math.asin(oy / d) + (e.movementY || 0) * 0.0022));
      W.cam.set(ex + d * Math.cos(el) * Math.sin(az), ey + d * Math.sin(el), ez + d * Math.cos(el) * Math.cos(az));
      const G = W.grid; if (G && (G.count > 0 || G.tiled)) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }
      const fx = ex - W.cam.x, fy = ey - W.cam.y, fz = ez - W.cam.z, fl = Math.hypot(fx, fy, fz) || 1;
      W.cyaw = Math.atan2(-fx, -fz); W.cpitch = Math.asin(fy / fl);
      walkStep(0); dirty = true;
      return;
    }
    lookBy(e.movementX || 0, e.movementY || 0);
  });
  // v46 : regard (souris, doigt) : mx, my en pixels de déplacement de la souris ; caméra libre, troisième personne (orbite autour de l'avatar), subjective
  function lookBy(mx, my) {
    if (W.view === 'free') {
      W.cyaw -= mx * 0.0022;
      W.cpitch = Math.max(-1.45, Math.min(1.45, W.cpitch - my * 0.0022));
      return;
    }
    if (W.view === 'tps') {   // v35 : la souris fait orbiter la caméra autour de l'avatar sans le tourner
      W.tyaw -= mx * 0.0022;
      W.tpitch = Math.max(-1.45, Math.min(1.45, W.tpitch - my * 0.0022));
      return;
    }
    W.yaw -= mx * 0.0022;
    W.pitch = Math.max(-1.45, Math.min(1.45, W.pitch - my * 0.0022));
  }
  // v46 : écran tactile en promenade : un doigt qui glisse sur la scène fait regarder (on tire le décor : doigt vers la droite, regard vers la gauche) ;
  // un seul doigt suivi ; les gestes de la vue globale restent ceux d'OrbitControls
  let touchLook = null;
  dom.addEventListener('pointerdown', e => { if (e.pointerType === 'touch' && walking && !touchLook) touchLook = { id: e.pointerId, x: e.clientX, y: e.clientY }; });
  dom.addEventListener('pointermove', e => {
    if (!touchLook || e.pointerId !== touchLook.id) return;
    if (!walking) { touchLook = null; return; }
    const dx = e.clientX - touchLook.x, dy = e.clientY - touchLook.y; touchLook.x = e.clientX; touchLook.y = e.clientY;
    if (dx || dy) { W.moved = true; lookBy(-dx * 1.6, -dy * 1.6); dirty = true; }
  });
  for (const ev of ['pointerup', 'pointercancel']) dom.addEventListener(ev, e => { if (touchLook && e.pointerId === touchLook.id) touchLook = null; });
  // v35 : molette en promenade. Caméra libre : avance / recule la caméra le long du regard (pas = 15 % de la distance à l'avatar, 0,5 à 20 m) ;
  // troisième personne : règle la distance de la caméra (1 à 30 m) ; vue subjective : rien. La page ne défile pas.
  window.addEventListener('wheel', e => {
    if (!walking) return;
    const t = e.target;
    if (t === dom || t === document.body || t === document.documentElement) e.preventDefault();
    if (t !== dom && t !== document.body && t !== document.documentElement) return;
    const sgn = Math.sign(e.deltaY); if (!sgn) return;
    if (W.view === 'tps') { setTpsDist(W.tdist * (sgn > 0 ? 1.15 : 1 / 1.15)); walkStep(0); dirty = true; }
    else if (W.view === 'free') {
      const dd = Math.hypot(W.cam.x - W.pos.x, W.cam.y - (W.pos.y + cfg.eyeHeight), W.cam.z - W.pos.z);
      const step = Math.max(0.5, Math.min(20, 0.15 * dd)) * -sgn;
      const cp = Math.cos(W.cpitch), sp = Math.sin(W.cpitch), sy = Math.sin(W.cyaw), cy = Math.cos(W.cyaw);
      const G = W.grid, hasGround = G && (G.count > 0 || G.tiled);
      const nx = W.cam.x - sy * cp * step, nz = W.cam.z - cy * cp * step;
      if (hasGround && G.tiled && G.pending(nx, nz)) markWait(nx, nz);
      else { W.cam.x = nx; W.cam.z = nz; W.cam.y += sp * step; }
      if (hasGround) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }
      walkStep(0); dirty = true;
    }
  }, { passive: false });
  // téléportation : double-clic (ou double-clic au centre si la souris est capturée)
  const tpRay = new THREE.Raycaster(), tpV = new THREE.Vector2();
  function walkTeleport(nx, ny) {
    if (!model || !walking) return false;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny);
    tpRay.setFromCamera(tpV, camera);
    const tokens = parseIgnore(cfg.walkIgnore);
    for (const h of tpRay.intersectObject(model, true)) {
      const o = h.object;
      if (!o.isMesh || !o.visible) continue;
      const m = Array.isArray(o.material) ? o.material[h.face ? h.face.materialIndex : 0] : o.material;
      if (m && (isFoliageName(m.name) || nameHas(m.name, tokens))) continue;
      let skip = false;
      if (tokens.length) for (let p = o; p; p = p.parent) if (nameHas(p.name, tokens)) { skip = true; break; }
      if (skip) continue;
      const n = h.face ? h.face.normal.clone().transformDirection(o.matrixWorld) : new THREE.Vector3(0, 1, 0);
      if (n.dot(tpRay.ray.direction) > 0) n.negate();
      let x = h.point.x, z = h.point.z; const y = h.point.y;
      if (n.y < 0.5) { const hl = Math.hypot(n.x, n.z) || 1; x += n.x / hl * 0.5; z += n.z / hl * 0.5; } // mur : on se place devant
      if (W.grid && W.grid.tiled && W.grid.pending(x, z)) { markWait(x, z); return false; }
      const g = W.grid ? W.grid.ground(x, z, y + STEP_UP + 0.05) : null;
      W.pos.set(x, g === null ? y : g, z); W.vy = 0; W.grounded = true;
      dom.style.transition = 'opacity .12s'; dom.style.opacity = '0.35';
      setTimeout(() => { dom.style.opacity = '1'; }, 120);
      dirty = true;
      return true;
    }
    return false;
  }
  // nom de l'élément visé (clic simple)
  function pickNdc(nx, ny) {
    if (!model) return null;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny); tpRay.setFromCamera(tpV, camera);
    for (const h of tpRay.intersectObject(model, true)) if (h.object.isMesh && h.object.visible) return describePick(h.object, h.point.toArray());
    return null;
  }
  function doPick(e, locked) {
    if (!onPick) return;
    const r = dom.getBoundingClientRect();
    const info = pickNdc(locked ? 0 : (e.clientX - r.left) / r.width * 2 - 1, locked ? 0 : -((e.clientY - r.top) / r.height) * 2 + 1);
    onPick(info, locked ? r.left + r.width / 2 : e.clientX, locked ? r.top + r.height / 2 : e.clientY);
  }
  let downPos = null, lastClick = { t: 0, x: 0, y: 0 };
  dom.addEventListener('pointerdown', e => { downPos = [e.clientX, e.clientY]; });
  dom.addEventListener('click', e => {
    if (linkLock) return;   // mode « Lier à un élément » : exclusif, aucun autre clic n'agit
    if (walking && e.altKey) { if (!W.moved) recenterCam(); return; }   // v35 : Alt + clic = caméra derrière l'avatar (Alt + glisser : orbite, pas de recentrage)
    const locked = document.pointerLockElement === dom, now = e.timeStamp || performance.now();
    {
      const rc = dom.getBoundingClientRect();
      const cnx = locked ? 0 : (e.clientX - rc.left) / rc.width * 2 - 1, cny = locked ? 0 : -((e.clientY - rc.top) / rc.height) * 2 + 1;
      const still = !!downPos && Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]) < 6;
      if (zones.length && onZone && (walking || (still && !zoneEditor))) {
        const zc = zoneFromClick(cnx, cny, walking ? zoneInfoDist() : 0, true);
        if (zc) { fireZone(zc, 'click'); return; }
      }
    }
    if (!walking) {
      const still = !!downPos && Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]) < 6;
      if (pickOrbit && onPick && still) doPick(e, false);
      return;
    }
    if (now - lastClick.t < 400 && (locked || Math.hypot(e.clientX - lastClick.x, e.clientY - lastClick.y) < 12)) {
      lastClick.t = 0;
      const r = dom.getBoundingClientRect();
      walkTeleport(locked ? 0 : (e.clientX - r.left) / r.width * 2 - 1, locked ? 0 : -((e.clientY - r.top) / r.height) * 2 + 1);
      if (onPick) onPick(null, 0, 0);
      return;
    }
    lastClick = { t: now, x: e.clientX, y: e.clientY };
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
    // un clic ne capture jamais la souris : seulement G ou le bouton « Capturer la souris » (grabMouse) ; sans capture, glisser bouton enfonce tourne la vue
    doPick(e, locked);
  });

  dom.addEventListener('dblclick', e => { if (!walking && !linkLock) setLanding(e); });

  // ---- présence : autres visiteurs (WebSocket)
  let uid = (() => {
    let u = ''; try { u = localStorage.getItem('glb2html_uid') || ''; } catch (_) {}
    if (u.length < 16) {
      const a = new Uint8Array(16);
      if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(a); else for (let i = 0; i < 16; i++) a[i] = Math.random() * 256;
      u = [...a].map(b => b.toString(16).padStart(2, '0')).join('');
      try { localStorage.setItem('glb2html_uid', u); } catch (_) {}
    }
    return u;
  })();
  const P = { ws: null, id: null, peers: new Map(), last: 0, name: '', state: 'off', retry: 0, timer: 0, sent: [0, 0, 0, 0], myColor: null, serverColor: null, opened: false, closeCode: null, closeReason: '', everOpened: false, stopped: false };
  const PRES_TRIES_NEVER = 5, PRES_TRIES_LOST = 12;   // essais de connexion consecutifs avant d'arreter jusqu'au rechargement : jamais ouverte / ouverte puis perdue
  const r2 = v => Math.round(v * 100) / 100;
  const cleanName = s => String(s || '').replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 24);
  function pStatus(state, reason, stopped) { P.state = state; if (onPresence) onPresence({ state, count: state === 'online' ? P.peers.size + (walking ? 1 : 0) : 0, spectator: !walking, reason: reason || '', stopped: !!stopped }); }
  function setMyName(n) { n = cleanName(n); if (!n) return; P.name = n; if (onName) onName(n); }
  function makeLabel(text) {
    const cv = document.createElement('canvas'); cv.width = 256; cv.height = 64;
    const g = cv.getContext('2d');
    g.fillStyle = 'rgba(255,255,255,0.92)'; g.fillRect(0, 0, 256, 64);
    g.strokeStyle = '#000'; g.lineWidth = 3; g.strokeRect(1.5, 1.5, 253, 61);
    g.fillStyle = '#000'; g.font = 'bold 30px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(text || '?', 128, 34, 240);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, fog: false }));
    sp.scale.set(1.6, 0.4, 1);
    return sp;
  }
  function makeAvatar(name, color) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.26, 0.85, 4, 12), new THREE.MeshStandardMaterial({ color, roughness: 0.7 }));
    body.position.y = 0.69; body.userData.tint = true; g.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf0c8a0, roughness: 0.8 }));
    head.position.y = 1.56; g.add(head);
    const nose = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 8), new THREE.MeshStandardMaterial({ color: 0x333333 }));
    nose.rotation.x = -Math.PI / 2; nose.position.set(0, 1.56, -0.2); g.add(nose);
    const label = makeLabel(name); label.position.y = 2.1; g.add(label);
    // losange flottant (style « plumbob ») à la couleur du visiteur, avec contour noir : visible sans dépendre de la couleur, masqué par les murs
    const beacon = new THREE.Group();
    const dia = new THREE.Mesh(new THREE.OctahedronGeometry(0.26, 0), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.95, fog: false }));
    dia.scale.y = 1.6; dia.userData.tint = true; beacon.add(dia);
    const edg = new THREE.LineSegments(new THREE.EdgesGeometry(dia.geometry), new THREE.LineBasicMaterial({ color: 0x000000, fog: false }));
    edg.scale.y = 1.6; beacon.add(edg);
    beacon.position.y = 2.75; g.add(beacon);
    g.userData.beacon = beacon;
    return g;
  }
  function makeBubble(text) {
    const m = document.createElement('canvas').getContext('2d'); m.font = '28px sans-serif';
    const lines = []; let cur = '';
    for (const w of String(text).split(/\s+/)) { const t = cur ? cur + ' ' + w : w; if (m.measureText(t).width > 470 && cur) { lines.push(cur); cur = w; } else cur = t; }
    if (cur) lines.push(cur);
    const shown = lines.slice(0, 4); if (lines.length > 4) shown[3] = shown[3].slice(0, 36) + '…';
    const lh = 36, h = shown.length * lh + 20;
    const cv = document.createElement('canvas'); cv.width = 512; cv.height = h;
    const g = cv.getContext('2d');
    g.fillStyle = 'rgba(255,255,255,0.95)'; g.fillRect(0, 0, 512, h);
    g.strokeStyle = '#000'; g.lineWidth = 4; g.strokeRect(2, 2, 508, h - 4);
    g.fillStyle = '#000'; g.font = '28px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    shown.forEach((l, i) => g.fillText(l, 256, 10 + lh / 2 + i * lh, 480));
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, fog: false }));
    sp.scale.set(2.56, h * 0.005, 1);
    sp.userData.isBubble = true; sp.userData.w = 2.56; sp.userData.h = h * 0.005;   // taille de base : agrandie avec le même k que le nom
    return sp;
  }
  // hauteurs (repère de l'avatar) du nom, de la bulle et du losange : bas, haut ; pour les tests
  function avatarStack(q) {
    const box = (o, half) => o ? { y: o.position.y, bottom: o.position.y - half, top: o.position.y + half } : null;
    const lab = q.g.children.find(o => o.isSprite && !o.userData.isBubble), bc = q.g.userData.beacon;
    return { label: box(lab, lab ? lab.scale.y / 2 : 0), bubble: box(q.bubble, q.bubble ? q.bubble.scale.y / 2 : 0), beacon: box(bc, bc ? 0.26 * 1.6 * bc.scale.y : 0), dist: camera.position.distanceTo(q.g.position) };
  }
  function removeBubble(q) { if (q.bubble) { q.g.remove(q.bubble); q.bubble.material.map.dispose(); q.bubble.material.dispose(); q.bubble = null; } }
  function showBubble(q, text) { removeBubble(q); q.bubble = makeBubble(text); q.bubbleUntil = cfg.chatFade > 0 ? performance.now() + cfg.chatFade * 1000 : Infinity; q.g.add(q.bubble); }
  function disposeAvatar(g) {
    scene.remove(g);
    g.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
  }
  function addPeer(q) {
    if (!q || q.id === P.id || P.peers.has(q.id)) return;
    const g = makeAvatar(q.name, q.color | 0); g.visible = false; scene.add(g);
    const peer = { id: q.id, name: q.name, color: q.color | 0, g, tx: 0, ty: 0, tz: 0, tyaw: 0 };
    if (Array.isArray(q.p)) { peer.tx = q.p[0]; peer.ty = q.p[1]; peer.tz = q.p[2]; peer.tyaw = q.yaw || 0; g.position.set(peer.tx, peer.ty, peer.tz); g.rotation.y = peer.tyaw; g.visible = true; }
    P.peers.set(q.id, peer);
  }
  // v34 : ma couleur choisie part au serveur au plus toutes les 300 ms (le sélecteur de couleur émet en continu) ; la dernière valeur part toujours (le serveur ignore deux changements à moins de 0,2 s)
  let colorT = 0, colorTimer = 0;
  function pushColor() {
    clearTimeout(colorTimer);
    if (P.myColor === null || !P.ws || P.ws.readyState !== 1 || !P.id) return;
    const wait = 300 - (performance.now() - colorT);
    if (wait > 0) { colorTimer = setTimeout(pushColor, wait); return; }
    colorT = performance.now(); P.ws.send(JSON.stringify({ t: 'color', color: P.myColor }));
  }
  // v34 : un visiteur change de couleur en cours de connexion : corps et losange prennent la nouvelle couleur
  function recolorPeer(q, color) { q.color = color; q.g.traverse(o => { if (o.userData.tint && o.material) o.material.color.setHex(color); }); dirty = true; }
  function removePeer(id) { const q = P.peers.get(id); if (q) { disposeAvatar(q.g); P.peers.delete(id); } }
  function clearPeers() { for (const id of [...P.peers.keys()]) removePeer(id); }
  function presenceMsg(m) {
    if (!m || typeof m !== 'object') return;
    if (m.t === 'welcome') {
      P.id = m.id; (m.peers || []).forEach(addPeer); pStatus('online'); dodgeWelcome();
      P.serverColor = Number.isInteger(m.color) && m.color >= 0 && m.color <= 0xFFFFFF ? m.color : null;
      if (m.name) setMyName(m.name);
      if (m.role === 'spectator' && walking && P.ws) P.ws.send(JSON.stringify({ t: 'role', walker: true, name: P.name }));
      if (onChat && cfg.chat !== false) (m.history || []).forEach(h => onChat({ id: h.id, name: cleanName(h.name) || '?', text: String(h.text || '').slice(0, 200), self: false, history: true, n: Number.isFinite(h.n) ? h.n : undefined, ts: Number.isFinite(h.t) ? h.t : undefined }));
    }
    else if (m.t === 'join') { const had = P.peers.has(m.id) || m.id === P.id; addPeer(m); pStatus('online'); if (onChat && cfg.chat !== false) onChat({ system: true, text: tr('core.joined', cleanName(m.name) || '?') }); if (!had && onPeer) onPeer('join', cleanName(m.name) || '?'); }   // v36 : onPeer = visiteur EN PROMENADE qui arrive ou part (jamais moi, jamais la liste initiale)
    else if (m.t === 'leave') { const q = P.peers.get(m.id); removePeer(m.id); pStatus('online'); if (q && onChat && cfg.chat !== false) onChat({ system: true, text: tr('core.left', q.name) }); if (q && onPeer) onPeer('leave', q.name); }
    else if (m.t === 'chat' && cfg.chat !== false) {
      const text = String(m.text || '').slice(0, 200), q = P.peers.get(m.id);
      if (q) showBubble(q, text);
      if (onChat) onChat({ id: m.id, name: cleanName(m.name) || (q && q.name) || '?', text, self: m.id === P.id, history: false, n: Number.isFinite(m.n) ? m.n : undefined, ts: Number.isFinite(m.ts) ? m.ts : undefined });
    }
    else if (m.t === 'history') {   // v37 : page plus ancienne de l'historique du salon (réponse à requestHistory)
      if (onHistory && cfg.chat !== false) onHistory({ more: m.more === true, msgs: (Array.isArray(m.msgs) ? m.msgs : []).slice(0, 100).map(h => ({ id: h.id, name: cleanName(h.name) || '?', text: String(h.text || '').slice(0, 200), self: false, history: true, n: Number.isFinite(h.n) ? h.n : undefined, ts: Number.isFinite(h.t) ? h.t : undefined })) });
    }
    else if (m.t === 'notice') { if (onChat && cfg.chat !== false) onChat({ system: true, text: String(m.text || '').slice(0, 120) }); }
    else if (m.t === 'pos') {
      const q = P.peers.get(m.id);
      if (q && Array.isArray(m.p) && m.p.every(Number.isFinite)) {
        q.tx = m.p[0]; q.ty = m.p[1]; q.tz = m.p[2]; q.tyaw = Number.isFinite(m.yaw) ? m.yaw : q.tyaw;
        if (!q.g.visible) { q.g.position.set(q.tx, q.ty, q.tz); q.g.rotation.y = q.tyaw; q.g.visible = true; }
      }
    }
    else if (m.t === 'name') {
      const q = P.peers.get(m.id);
      if (q) { q.name = cleanName(m.name); const old = q.g.children.find(o => o.isSprite && !o.userData.isBubble); if (old) { q.g.remove(old); old.material.map.dispose(); old.material.dispose(); } const l = makeLabel(q.name); l.position.y = 2.1; q.g.add(l); }
    }
    else if (m.t === 'you') { setMyName(m.name); }
    else if (m.t === 'color') {
      const q = P.peers.get(m.id);
      if (q && Number.isInteger(m.color) && m.color >= 0 && m.color <= 0xFFFFFF) recolorPeer(q, m.color);
    }
    else if (m.t === 'kicked' || m.t === 'banned') {
      P.blocked = true;
      let r = String(m.reason || '').slice(0, 120);
      if (m.t === 'banned' && m.until) r += tr('core.ban.until', new Date(m.until * 1000).toLocaleString(i18nLocale));
      pStatus(m.t, r);
    }
    else if (m.t === 'refused') {   // v51 : refus d'un serveur à créateurs (origine non déclarée, créateur suspendu, salon hors préfixe, trop de salons) : pas de nouvelle tentative
      P.blocked = true;
      const RF = { origin: tr('core.pres.refused.origin'), off: tr('core.pres.refused.off'), room: tr('core.pres.refused.room'), rooms: tr('core.pres.refused.rooms') };
      pStatus('refused', RF[m.why] || tr('core.pres.refused.unknown'));
    }
    else if (m.t === 'full') { pStatus('full'); }
    dirty = true;
  }
  // v51 : adresse de présence ; « * » à la place du nom = le même nom que la page (la présence au même endroit que la page ; disque et viewer : 127.0.0.1) ; 0.0.0.0 -> 127.0.0.1
  function presUrl(u) { return String(u || '').trim().replace(/^(wss?:\/\/)(\*|0\.0\.0\.0)(?=[:/]|$)/i, (m, p, h) => p + (h === '*' ? (location.hostname || '127.0.0.1') : '127.0.0.1')); }
  function presenceConnect() {
    if (!cfg.presenceUrl || P.ws) return;
    P.blocked = false; P.opened = false; P.stopped = false; P.closeCode = null; P.closeReason = '';
    pStatus('connecting');
    let ws;
    try { ws = new WebSocket(presUrl(cfg.presenceUrl)); } catch (e) { pStatus('error', e && e.name === 'SecurityError' ? tr('core.pres.secerr') : tr('core.pres.never')); return; }
    P.ws = ws;
    ws.onopen = () => { P.retry = 0; P.opened = true; P.everOpened = true; { const h = { t: 'hello', room: cfg.room || cfg.roomDefault || '', name: P.name, uid, spectator: !walking }; if (P.myColor !== null) h.color = P.myColor; ws.send(JSON.stringify(h)); } };
    ws.onmessage = ev => { let m; try { m = JSON.parse(ev.data); } catch (_) { return; } presenceMsg(m); };
    ws.onerror = () => {};
    ws.onclose = ev => {
      if (P.ws !== ws) return;
      const code = ev && Number.isInteger(ev.code) ? ev.code : null, why = String((ev && ev.reason) || '').slice(0, 120);   // v45 : code et raison de la fermeture (jamais ouverte : le navigateur donne 1006 sans raison)
      P.closeCode = code; P.closeReason = why;
      P.ws = null; P.id = null; clearPeers();
      if (P.blocked) return;
      if ((walking || spectateOn) && P.state !== 'full') {
        const why2 = P.opened ? tr('core.pres.closed', code === null ? '?' : code, why ? ' : ' + why : '') : tr('core.pres.never');
        clearTimeout(P.timer);
        if (P.retry + 1 >= (P.everOpened ? PRES_TRIES_LOST : PRES_TRIES_NEVER)) { P.stopped = true; pStatus('error', why2, true); }   // essais arretes jusqu'au rechargement de la page (ou jusqu'a un nouveau passage en promenade)
        else { pStatus('error', why2); P.timer = setTimeout(presenceConnect, Math.min(15000, 1500 * (++P.retry))); }
      }
      else if (!walking) pStatus('off');
    };
  }
  function presenceEnter() {
    if (!cfg.presenceUrl) return;
    if (P.ws && P.ws.readyState === 1 && P.id) { P.ws.send(JSON.stringify({ t: 'role', walker: true, name: P.name })); pStatus('online'); }
    else if (!P.ws) presenceConnect();
  }
  function presenceLeave() {
    if (spectateOn && P.ws && P.ws.readyState === 1) { P.ws.send(JSON.stringify({ t: 'role', walker: false })); pStatus('online'); }
    else presenceDisconnect();
  }
  function presenceDisconnect() {
    clearTimeout(P.timer);
    const ws = P.ws; P.ws = null; P.id = null;
    if (ws) { try { ws.close(); } catch (_) {} }
    clearPeers(); if (P.state !== 'off') pStatus('off');
  }
  // v37 : alerte « pseudo cité » : demi-seconde visible, demi-seconde cachée, SANS limite de durée, jusqu'à ma première action (touche, clic, mouvement de l'avatar, envoi) ;
  // concerne l'étiquette du nom de l'auteur, sa bulle (si elle existe encore) et, côté page, la ligne du message (onBlink / onBlinkEnd). Plusieurs citations : toutes clignotent.
  const BL = { on: false, t0: 0, vis: true, px: 0, pz: 0, yaw: 0 };
  function blinkStop() {
    if (!BL.on) return;
    BL.on = false; BL.vis = true;
    for (const q of P.peers.values()) {
      if (!q.blink) continue;
      q.blink = null;
      const lab = q.g.children.find(o => o.isSprite && !o.userData.isBubble); if (lab) lab.visible = true;
      if (q.bubble) q.bubble.visible = true;
    }
    dirty = true;
    if (onBlinkEnd) onBlinkEnd();
  }
  function blinkStart(id) {
    const q = id === undefined ? null : P.peers.get(id);
    if (!BL.on) { BL.on = true; BL.t0 = performance.now(); BL.vis = true; BL.px = W.pos.x; BL.pz = W.pos.z; BL.yaw = W.yaw; }
    if (q) { q.blink = { t0: BL.t0 }; q.blinkHidden = q.blinkHidden || 0; }
    dirty = true;
    return !!q;
  }
  function blinkTick(now) {
    if (!BL.on) return;
    if (walking && (Math.hypot(W.pos.x - BL.px, W.pos.z - BL.pz) > 0.05 || Math.abs(Math.atan2(Math.sin(W.yaw - BL.yaw), Math.cos(W.yaw - BL.yaw))) > 0.02)) { blinkStop(); return; }
    const v = Math.floor((now - BL.t0) / 500) % 2 === 0;
    if (v !== BL.vis) {
      BL.vis = v; dirty = true;
      if (!v) for (const q of P.peers.values()) if (q.blink) q.blinkHidden = (q.blinkHidden || 0) + 1;
      if (onBlink) onBlink(v);
    }
  }
  for (const ev of ['keydown', 'pointerdown']) window.addEventListener(ev, e => { if (BL.on) blinkStop(); }, true);
  function presenceTick(dt, now) {
    blinkTick(now);
    if (P.peers.size) {
      const a = 1 - Math.exp(-dt * 10);
      for (const q of P.peers.values()) {
        if (q.bubble && now > q.bubbleUntil) removeBubble(q);
        if (!q.g.visible) continue;
        q.g.position.x += (q.tx - q.g.position.x) * a; q.g.position.y += (q.ty - q.g.position.y) * a; q.g.position.z += (q.tz - q.g.position.z) * a;
        const d = Math.atan2(Math.sin(q.tyaw - q.g.rotation.y), Math.cos(q.tyaw - q.g.rotation.y));
        q.g.rotation.y += d * a;
        const dist = camera.position.distanceTo(q.g.position), k = Math.max(1, dist / 28);
        const lab = q.g.children.find(o => o.isSprite && !o.userData.isBubble), bc = q.g.userData.beacon;
        if (q.blink) { if (lab) lab.visible = BL.vis; if (q.bubble) q.bubble.visible = BL.vis; }   // v37 : étiquette du nom et bulle clignotent ensemble
        const ks = Math.max(1, dist / 45), ly = 2.1 + 0.55 * (k - 1);
        if (lab) { lab.scale.set(1.6 * k, 0.4 * k, 1); lab.position.y = ly; }
        // pile de bas en haut : nom, bulle (si elle existe), losange, avec une marge entre chacun ; tailles réelles des sprites (scale.y)
        let top = ly + 0.2 * k;                                        // haut du nom
        if (q.bubble) {
          const u = q.bubble.userData; q.bubble.scale.set(u.w * k, u.h * k, 1);
          q.bubble.position.y = top + 0.1 * k + q.bubble.scale.y / 2; top = q.bubble.position.y + q.bubble.scale.y / 2;
        }
        if (bc) {
          bc.scale.setScalar(ks);
          const want = top + 0.5 * ks;                                  // sans bulle : ly + 0,2 k + 0,5 ks, comme avant
          bc.position.y = q.bcY === undefined ? want : q.bcY + (want - q.bcY) * (1 - Math.exp(-dt * 12));   // glisse à l'apparition / disparition de la bulle
          q.bcY = bc.position.y; bc.rotation.y += dt * 1.2;
        }
      }
      dirty = true;
    }
    if (walking && P.ws && P.ws.readyState === 1 && P.id && now - P.last > 90) {
      const cur = [r2(W.pos.x), r2(W.pos.y), r2(W.pos.z), r2(W.yaw)], s = P.sent;
      if (now - P.last > 1000 || cur.some((v, i) => Math.abs(v - s[i]) > 0.004)) {
        P.last = now; P.sent = cur;
        P.ws.send(JSON.stringify({ t: 'pos', p: cur.slice(0, 3), yaw: cur[3] }));
      }
    }
  }

  // ---- zones : panneaux, portails, liens, commandes
  const zoneGroup = new THREE.Group(); scene.add(zoneGroup);
  let selId = null;
  let zones = [], zoneHit = [], zoneAll = [], zoneInside = new Set(), nearZone = null, zoneEditor = false, selBox = null, onZone = null, onNear = null;
  // zones liées à un élément du modèle (champ mesh = nom exact) : id de zone -> { meshes, box } ; mesh 3D -> zone
  const zoneLink = new Map(), meshZone = new Map();
  const zoneOf = o => o.userData.zone || meshZone.get(o) || null;
  // boîte englobante (monde) de ces meshes, matrices à jour depuis la racine (modèle recentré, décalé ou mis à l'échelle) ; null si vide
  function boxOfMeshes(meshes) {
    if (model) model.updateMatrixWorld(true);
    const b = new THREE.Box3();
    for (const m of meshes) b.expandByObject(m);
    return b.isEmpty() || !Number.isFinite(b.min.x + b.max.x + b.min.y + b.max.y + b.min.z + b.max.z) ? null : b;
  }
  function findMeshes(ref) {
    const out = new Set();
    // mode tuiles : nœuds des tuiles chargées dont extras.ref est exactement la référence (calculée par glb2tiles sur le GLB entier)
    const objs = TL.on ? (TL.refIndex.get(ref) || []) : resolveMeshRef(model, ref);
    for (const o of objs) o.traverse(c => { if (c.isMesh) out.add(c); });
    return [...out];
  }
  // boîte (monde) de l'élément : en mode tuiles, celle de l'objet ENTIER (extras.box, même si une partie seulement est chargée), sinon celle des morceaux
  function refBox(ref, meshes) {
    if (TL.on && TL.root) {
      for (const o of TL.refIndex.get(ref) || []) {
        const b = o.userData.box;
        if (!Array.isArray(b) || b.length !== 6 || !b.every(Number.isFinite)) continue;
        TL.root.updateMatrixWorld(true);
        const box = new THREE.Box3(), v = new THREE.Vector3();
        for (let k = 0; k < 8; k++) box.expandByPoint(v.set(k & 1 ? b[3] : b[0], k & 2 ? b[4] : b[1], k & 4 ? b[5] : b[2]).applyMatrix4(TL.root.matrixWorld));
        return box;
      }
    }
    return boxOfMeshes(meshes);
  }
  function resolveLinks() {
    zoneLink.clear();
    for (const z of zones) {
      if (!z.mesh || z.type === 'spawn') continue;
      const meshes = findMeshes(z.mesh);
      if (!meshes.length) { if (!TL.on) console.warn(tr('core.zone.nomesh', z.id, z.mesh)); continue; }
      const box = refBox(z.mesh, meshes);
      if (!box) { console.warn(tr('core.zone.nogeom', z.id, z.mesh)); continue; }
      zoneLink.set(z.id, { meshes, box });
    }
    TL.linkSig = linkSignature();
  }
  // contour d'un élément (noir + blanc décalé, lisible sur tout fond)
  function outlineOf(box) {
    const g = new THREE.Group();
    for (const [b, c] of [[box.clone(), 0x000000], [box.clone().expandByScalar(0.05), 0xffffff]]) {
      const h = new THREE.Box3Helper(b, c); h.material.depthTest = false; h.material.transparent = true; h.material.fog = false; h.renderOrder = 999; g.add(h);
    }
    return g;
  }
  const hoverG = new THREE.Group(); hoverG.visible = false; scene.add(hoverG);
  let hoverZone = null, hoverT = 0;
  // page exportée : marqueur discret au sol (id de zone -> matériaux), infobulle au survol
  const MARK_OP = 0.4, markerMat = new Map();
  let tipEl = null;
  function zoneTipText(z) {
    const name = z.label || z.id;
    if (z.type === 'url') return [name, z.target];
    if (z.type === 'ha') return [name, tr('core.tip.cmd', name)];
    return [name, tr('core.tip.region', (String(z.target || '').trim() || tr('core.tip.thisregion')) + (z.spawn ? ' #' + z.spawn : ''))];
  }
  function tipShow(z, cx, cy) {
    if (!z) { if (tipEl) tipEl.hidden = true; return; }
    if (!tipEl) {
      tipEl = document.createElement('div'); tipEl.id = 'zoneTip';
      tipEl.style.cssText = 'position:fixed;left:0;top:0;z-index:40;pointer-events:none;max-width:min(420px,90vw);overflow-wrap:anywhere;font:12px/1.4 ui-monospace,Consolas,monospace;background:#000;color:#fff;border:1px solid #fff;border-radius:6px;padding:5px 9px';
      document.body.appendChild(tipEl);
    }
    const [t, sub] = zoneTipText(z);
    const ds = tipObj ? ' · ' + tr('core.tip.dist', coneDist(tipObj)) : '';   // v37 : distance au visiteur, mise à jour à chaque mouvement
    const key = z.id + '|' + ds;
    if (tipEl.dataset.zone !== key) {
      tipEl.dataset.zone = key; tipEl.textContent = '';
      const b = document.createElement('b'); b.textContent = sub ? t : t + ds; tipEl.appendChild(b);
      if (sub) { tipEl.appendChild(document.createElement('br')); tipEl.appendChild(document.createTextNode(sub + ds)); }
    }
    tipEl.hidden = false;
    const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
    tipEl.style.left = Math.max(4, Math.min(innerWidth - w - 4, cx + 14)) + 'px';
    tipEl.style.top = Math.max(4, Math.min(innerHeight - h - 4, cy + 18)) + 'px';
  }
  const ZONE_TYPES = ['url', 'ha', 'portal', 'spawn'];
  const slug = s => String(s || '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
  function cleanZone(z, i) {
    const num = (v, d, lo, hi) => { v = Number(v); return Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : d; };
    const type = ZONE_TYPES.includes(z.type) ? z.type : 'portal';
    const o = {
      id: slug(z.id) || ('z' + (i + 1)), type, label: String(z.label || '').slice(0, 60),
      x: num(z.x, 0, -1e5, 1e5), y: num(z.y, 0, -1e5, 1e5), z: num(z.z, 0, -1e5, 1e5), yaw: num(z.yaw, 0, -7, 7),
      shape: z.shape === 'board' ? 'board' : 'ring', trigger: ['click', 'enter', 'both'].includes(z.trigger) ? z.trigger : 'click',
      radius: num(z.radius, 2, 0.5, 50), w: num(z.w, 2.4, 0.5, 10), h: num(z.h, 1.2, 0.3, 6),
      target: String(z.target || '').slice(0, 600), spawn: slug(z.spawn), confirm: !!z.confirm, private: !!z.private, showName: !!z.showName,
      mesh: type === 'spawn' ? '' : String(z.mesh || '').replace(/[\u0000-\u001f]/g, '').slice(0, 200)
    };
    if (type !== 'portal') o.trigger = 'click';
    return o;
  }
  function boardTex(label, sub, w, h) {
    const W2 = 512, H2 = Math.max(96, Math.round(512 * h / w));
    const cv = document.createElement('canvas'); cv.width = W2; cv.height = H2;
    const g = cv.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, W2, H2);
    g.strokeStyle = '#000'; g.lineWidth = 10; g.strokeRect(5, 5, W2 - 10, H2 - 10);
    g.fillStyle = '#000'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = 'bold 46px sans-serif';
    const words = String(label).split(/\s+/), lines = []; let cur = '';
    for (const w3 of words) { const t = cur ? cur + ' ' + w3 : w3; if (g.measureText(t).width > W2 - 60 && cur) { lines.push(cur); cur = w3; } else cur = t; }
    if (cur) lines.push(cur);
    const shown = lines.slice(0, 3), lh = 54, y0 = H2 / 2 - 14 - (shown.length - 1) * lh / 2;
    shown.forEach((l, i) => g.fillText(l, W2 / 2, y0 + i * lh, W2 - 60));
    g.font = '28px sans-serif'; g.fillText(sub, W2 / 2, H2 - 34, W2 - 60);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    return tex;
  }
  // v36 : repère de portail (page exportée seulement) : petit cône pointé vers le bas (0,35 m de large, 0,5 m de haut), sommet à 2,0 m au-dessus du centre de la zone,
  // teinte claire neutre avec contour sombre (lisible sans dépendre de la couleur). Au-dessus de chaque portail et de chaque zone « enter » ou « both » ; les arrivées
  // n'en ont qu'avec --show-spawns (cfg.showSpawns). Visible jusqu'à zoneInfoDist en promenade ; T affiche / masque tous les cônes (choix mémorisé, défaut cfg.zoneCone).
  let coneOn = (() => { let v = cfg.zoneCone !== false; try { const s = localStorage.getItem('glb2html_cones'); if (s === '0' || s === '1') v = s === '1'; } catch (_) {} return v; })();
  let onCones = null;
  function coneFor(g, z, box) {
    if (zoneEditor) return false;
    if (!(z.type === 'spawn' ? cfg.showSpawns : (z.type === 'portal' || z.trigger !== 'click'))) return false;
    const geo = new THREE.ConeGeometry(0.175, 0.5, 16);
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xe8e8e8, fog: false }));
    m.rotation.x = Math.PI;   // pointe vers le bas
    if (box) m.position.set((box.min.x + box.max.x) / 2, box.max.y + 0.75, (box.min.z + box.max.z) / 2); else m.position.set(0, 2.25, 0);
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0x111111, fog: false })));
    m.userData.cone = true; m.userData.zone = z; m.visible = coneOn; m.userData.base = m.position.clone();
    g.add(m); zoneLabs.push(m); zoneAll.push(m);
    if (z.type !== 'spawn') zoneHit.push(m);
    return true;
  }
  // v37 : taille apparente constante : l'échelle suit la distance à la caméra (distance / 12, entre 1 et 12), la pointe reste au même point
  function coneScaleTick() {
    for (const o of zoneLabs) {
      if (!o.userData.cone || !o.visible || !o.parent) continue;
      const b = o.userData.base, px = o.parent.position.x + b.x, py = o.parent.position.y + b.y, pz = o.parent.position.z + b.z;
      const d = Math.hypot(camera.position.x - px, camera.position.y - py, camera.position.z - pz);
      const k = Math.min(12, Math.max(1, d / 12));
      if (Math.abs(o.scale.x - k) > 1e-3) { o.scale.setScalar(k); o.position.y = b.y - 0.25 + 0.25 * k; }
    }
  }
  // distance affichée dans l'infobulle d'un cône : promeneur -> cône, sinon caméra -> cône (arrondie au mètre)
  function coneDist(o) {
    const b = o.userData.base, p = o.parent ? o.parent.position : { x: 0, y: 0, z: 0 }, ref = walking ? W.pos : camera.position;
    return Math.round(Math.hypot(ref.x - (p.x + b.x), ref.y - (p.y + b.y), ref.z - (p.z + b.z)));
  }
  function setCones(on, quiet) {
    coneOn = !!on; try { localStorage.setItem('glb2html_cones', coneOn ? '1' : '0'); } catch (_) {}
    zoneLabelTick(); if (hoverZone) setHover(null); dirty = true;
    if (onCones && !quiet) onCones(coneOn);
    return coneOn;
  }
  window.addEventListener('keydown', e => {
    if (e.code === 'KeyT' && !e.repeat && !typing(e) && !e.ctrlKey && !e.metaKey && !e.altKey && !zoneEditor && zones.length) setCones(!coneOn);
  });
  function buildZones() {
    for (const c of [...zoneGroup.children]) {
      zoneGroup.remove(c);
      c.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
    }
    if (selBox) { scene.remove(selBox); selBox.geometry.dispose(); selBox.material.dispose(); selBox = null; }
    zoneHit = []; zoneAll = []; zoneLabs = []; meshZone.clear();
    setHover(null);
    markerMat.clear();
    for (const z of zones) {
      if (zoneOff(z)) continue;   // mode tuiles : zone liée à un objet dont aucune tuile n'est chargée
      const link = zoneLink.get(z.id);
      const g = new THREE.Group(); g.userData.zoneId = z.id;
      if (!link) { g.position.set(z.x, z.y, z.z); g.rotation.y = z.yaw; }
      const kind = { url: tr('core.kind.url'), ha: tr('core.kind.ha'), portal: tr('core.kind.portal'), spawn: tr('core.kind.spawn') }[z.type];
      const priv = zoneEditor && z.private ? tr('core.private') : '';
      const clickable = z.type !== 'spawn' && z.trigger !== 'enter';
      let main = null;
      if (link) {
        // zone liée à un élément : l'élément est la zone (cliquable, E à moins de radius m). Aucun objet ajouté dans la page exportée.
        for (const m of link.meshes) if (!meshZone.has(m)) meshZone.set(m, z);
        zoneAll.push(...link.meshes); if (clickable) zoneHit.push(...link.meshes);
        const hasCone = coneFor(g, z, link.box);
        if (!zoneEditor && !z.showName && !hasCone) continue;
        if (zoneEditor) g.add(outlineOf(link.box));
        if (zoneEditor || z.showName) { const lab = makeLabel(zoneEditor ? (z.label || kind) + ' ⇢ ' + z.mesh + priv : (z.label || z.id)); lab.position.set((link.box.min.x + link.box.max.x) / 2, link.box.max.y + 0.9, (link.box.min.z + link.box.max.z) / 2); g.add(lab); if (!zoneEditor) zoneLabs.push(lab); }
        zoneGroup.add(g);
        continue;
      }
      if (z.type === 'spawn') {
        if (!zoneEditor) {
          // page exportée : les arrivées ne sont jamais dessinées, sauf avec --show-spawns (cfg.showSpawns) : petit marqueur discret au sol
          if (!cfg.showSpawns) continue;
          const sm = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: MARK_OP, side: THREE.DoubleSide, depthWrite: false, fog: false });
          const sd = new THREE.Mesh(new THREE.CircleGeometry(0.15, 24), sm); sd.rotation.x = -Math.PI / 2; sd.position.y = 0.04; sd.userData.marker = 'spawn'; g.add(sd);
          const sr = new THREE.Mesh(new THREE.RingGeometry(0.15, 0.2, 24), sm.clone()); sr.material.color.set(0xffffff); sr.rotation.x = -Math.PI / 2; sr.position.y = 0.045; sr.userData.marker = 'spawn'; g.add(sr);
          coneFor(g, z);
          zoneGroup.add(g);
          continue;
        }
        const cone = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.9, 12), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, depthTest: false, fog: false }));
        cone.rotation.x = -Math.PI / 2; cone.position.y = 0.6; g.add(cone); main = cone;
        const l = makeLabel(tr('core.spawn.label', z.id)); l.position.y = 1.7; g.add(l);
      } else if (zoneEditor) {
        // éditeur : le cylindre (portée de la zone) reste toujours visible, pour repérer et positionner ; le panneau s'y ajoute
        if (z.shape === 'board') {
          const sub = kind + (clickable ? tr('core.clickable') : '') + priv;
          const plane = new THREE.Mesh(new THREE.PlaneGeometry(z.w, z.h), new THREE.MeshBasicMaterial({ map: boardTex(z.label || kind, sub, z.w, z.h), side: THREE.DoubleSide, fog: false }));
          plane.position.y = 0.9 + z.h / 2; g.add(plane); main = plane;
          const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.92, 0.1), new THREE.MeshStandardMaterial({ color: 0x333333 })); post.position.y = 0.46; g.add(post);
        }
        const rad = z.shape === 'board' ? Math.max(z.radius, 2) : z.radius;
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, 2.4, 48, 1, true), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false, fog: false }));
        cyl.position.y = 1.2; g.add(cyl); if (!main) main = cyl; else { cyl.userData.zone = z; zoneAll.push(cyl); }
        const r1 = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.05, rad - 0.16), rad, 64), new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide, fog: false }));
        r1.rotation.x = -Math.PI / 2; r1.position.y = 0.05; g.add(r1);
        const r2 = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.02, rad - 0.3), Math.max(0.04, rad - 0.16), 64), new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: false }));
        r2.rotation.x = -Math.PI / 2; r2.position.y = 0.055; g.add(r2);
        if (z.shape !== 'board') { const lab = makeLabel((z.label || kind) + priv); lab.position.y = 2.9; g.add(lab); }
      } else if (z.showName && z.shape === 'board') {
        // page exportée, « Toujours afficher le nom » : le panneau
        const plane = new THREE.Mesh(new THREE.PlaneGeometry(z.w, z.h), new THREE.MeshBasicMaterial({ map: boardTex(z.label || kind, kind + (clickable ? tr('core.clickable') : ''), z.w, z.h), side: THREE.DoubleSide, fog: false }));
        plane.position.y = 0.9 + z.h / 2; g.add(plane); main = plane; zoneLabs.push(plane);
        const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.92, 0.1), new THREE.MeshStandardMaterial({ color: 0x333333 })); post.position.y = 0.46; g.add(post); zoneLabs.push(post);
      } else {
        // page exportée, selon cfg.zoneMarker : « dot » (défaut) disque plat 0,4 m + anneau fin ; « range » anneau fin et net au rayon réel de la zone
        // (visible de loin, sans cylindre) ; « none » rien. La zone de visée plus large et invisible reste dans les trois cas.
        const mkind = cfg.zoneMarker === 'range' || cfg.zoneMarker === 'none' ? cfg.zoneMarker : 'dot';
        if (mkind === 'dot') {
          const mat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: MARK_OP, side: THREE.DoubleSide, depthWrite: false, fog: false });
          const disc = new THREE.Mesh(new THREE.CircleGeometry(0.2, 32), mat); disc.rotation.x = -Math.PI / 2; disc.position.y = 0.04; disc.userData.marker = 'disc'; g.add(disc);
          const ring = new THREE.Mesh(new THREE.RingGeometry(0.2, 0.26, 32), mat.clone()); ring.material.color.set(0xffffff); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.045; ring.userData.marker = 'ring'; g.add(ring);
          markerMat.set(z.id, [mat, ring.material]);
        } else if (mkind === 'range') {
          const rad = z.shape === 'board' ? Math.max(z.radius, 2) : z.radius;
          const rb = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.02, rad - 0.1), rad, 96), new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide, fog: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
          rb.rotation.x = -Math.PI / 2; rb.position.y = 0.05; rb.userData.marker = 'range'; rb.userData.radius = rad; g.add(rb);
          const rw = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.01, rad - 0.17), Math.max(0.02, rad - 0.1), 96), new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
          rw.rotation.x = -Math.PI / 2; rw.position.y = 0.055; rw.userData.marker = 'range'; g.add(rw);
          const pts = []; for (let i = 0; i < 96; i++) { const a = i / 96 * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * rad, 0.06, Math.sin(a) * rad)); }
          const ln = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x000000, fog: false })); ln.userData.marker = 'range'; g.add(ln);   // trait d'un pixel : reste visible de très loin
        }
        if (clickable) {
          // v34 : zone de survol et de clic = l'anneau visible avec « range » (rayon réel de la zone) ; avec « dot » un peu plus large qu'avant (0,6 m au moins, 1 m au plus)
          const hr = mkind === 'range' ? (z.shape === 'board' ? Math.max(z.radius, 2) : z.radius) : (mkind === 'dot' ? Math.max(0.6, Math.min(z.radius, 1)) : 0.6);
          const hit = new THREE.Mesh(new THREE.CircleGeometry(hr, hr > 1 ? 48 : 16), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide })); hit.visible = false;
          hit.rotation.x = -Math.PI / 2; hit.position.y = 0.06; g.add(hit); main = hit;
        }
        if (z.showName) { const lab = makeLabel(z.label || z.id); lab.position.y = 1.2; g.add(lab); zoneLabs.push(lab); }
      }
      coneFor(g, z);
      if (main) { main.userData.zone = z; zoneAll.push(main); if (clickable) zoneHit.push(main); }
      zoneGroup.add(g);
    }
    dirty = true;
  }
  const tilesNoRefs = z => tr('core.zone.norefs', z.id, z.mesh);
  function setZones(list, opts) {
    zoneEditor = !!(opts && opts.editor);
    const seen = new Set();
    zones = (Array.isArray(list) ? list : []).map((z, i) => cleanZone(z || {}, i)).map(z => {
      let id = z.id, n = 2; while (seen.has(id)) id = z.id + '-' + (n++);
      seen.add(id); z.id = id; return z;
    }).filter(z => {
      if (TL.on && TL.refsKnown && !TL.refs && z.mesh && z.type !== 'spawn') { console.warn(tilesNoRefs(z)); return false; }
      return true;
    });
    nearZone = null; zoneInside.clear();
    resolveLinks();
    buildZones();
    return zones.map(z => Object.assign({}, z));
  }
  function zoneSelect(id) {
    selId = id;
    if (selBox) { scene.remove(selBox); selBox.geometry.dispose(); selBox.material.dispose(); selBox = null; }
    const g = zoneGroup.children.find(c => c.userData.zoneId === id);
    const zl = g && zoneLink.get(id);
    if (zl) { selBox = new THREE.Box3Helper(zl.box.clone(), 0x000000); selBox.material.depthTest = false; selBox.material.transparent = true; selBox.material.fog = false; selBox.renderOrder = 999; scene.add(selBox); }
    else if (g) { selBox = new THREE.BoxHelper(g, 0x000000); selBox.material.depthTest = false; selBox.material.transparent = true; scene.add(selBox); }
    dirty = true;
  }
  function fireZone(z, how) {
    if (walking && P.ws && P.ws.readyState === 1 && P.id) P.ws.send(JSON.stringify({ t: 'zone', id: z.id, type: z.type, label: z.label }));
    if (onZone) onZone(z, how);
  }
  // v35 : distance de survol et de clic des zones en promenade (config zoneInfoDist, 5 à 500 m, défaut 150 depuis la v37) ; les noms affichés (showName) la suivent
  const zoneInfoDist = () => Math.max(5, Math.min(500, Number(cfg.zoneInfoDist) || 150));
  let zoneLabs = [];
  function zoneLabelTick() {
    for (const o of zoneLabs) { let v = !walking || !o.parent || Math.hypot(W.pos.x - (o.parent.position.x + o.position.x), W.pos.z - (o.parent.position.z + o.position.z)) <= zoneInfoDist(); if (o.userData.cone) v = v && coneOn; if (o.visible !== v) { o.visible = v; dirty = true; } }
  }
  let lastHitObj = null, tipObj = null;
  function zoneFromClick(nx, ny, maxDist, forClick) {
    if (!zoneHit.length) return null;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny); tpRay.setFromCamera(tpV, camera);
    // v36 : un cône masqué (T) ne répond pas ; le cône d'un portail « enter » seul n'a qu'une infobulle (pas de clic)
    const h = tpRay.intersectObjects(zoneHit, false).find(q => !(q.object.userData.cone && (!q.object.visible || !coneOn || (forClick && q.object.userData.zone.trigger === 'enter'))));
    lastHitObj = null;
    if (!h || (maxDist && h.distance > maxDist)) return null;
    lastHitObj = h.object;
    const z = zoneOf(h.object), link = z && zoneLink.get(z.id);
    if (model) {
      // un élément traversable (walkIgnore) ne bloque pas le clic, ni les autres morceaux de l'élément visé
      const tokens = parseIgnore(cfg.walkIgnore);
      for (const m of tpRay.intersectObject(model, true)) {
        if (m.distance >= h.distance - 0.05) break;
        if (isIgnoredMesh(m.object, tokens) || (link && link.meshes.includes(m.object))) continue;
        return null;
      }
    }
    return z;
  }
  function setHover(z, cx, cy) {
    if (z && cx !== undefined) tipShow(z, cx, cy);
    if (z === hoverZone) return;
    if (hoverZone) for (const m of markerMat.get(hoverZone.id) || []) m.opacity = MARK_OP;
    if (!z) tipShow(null);
    hoverZone = z;
    if (z) { const mm = markerMat.get(z.id); if (mm) for (const m of mm) m.opacity = 0.8; }
    const link = z && zoneLink.get(z.id);
    hoverG.visible = !!link;
    if (link) { hoverG.clear(); hoverG.add(outlineOf(link.box)); }
    dom.style.cursor = z ? 'pointer' : '';
    dirty = true;
  }
  dom.addEventListener('pointermove', e => {
    if (linkLock || zoneEditor || !onZone || !zoneHit.length || e.buttons || document.pointerLockElement === dom) { if (hoverZone) setHover(null); return; }
    const now = performance.now(); if (now - hoverT < 50) return; hoverT = now;
    const r = dom.getBoundingClientRect();
    const zh = zoneFromClick((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1, walking ? zoneInfoDist() : 0);
    tipObj = zh && lastHitObj && lastHitObj.userData.cone ? lastHitObj : null;
    setHover(zh, e.clientX, e.clientY);
  });
  dom.addEventListener('pointerleave', () => setHover(null));
  function zonePickAt(cx, cy) {
    if (!zoneAll.length) return null;
    const r = dom.getBoundingClientRect();
    camera.updateMatrixWorld(true);
    tpV.set((cx - r.left) / r.width * 2 - 1, -((cy - r.top) / r.height) * 2 + 1); tpRay.setFromCamera(tpV, camera);
    const h = tpRay.intersectObjects(zoneAll, false)[0];
    return h ? zoneOf(h.object) : null;
  }
  // distance horizontale du marcheur à la zone (ou à son élément s'il est lié) et écart vertical (0 = à hauteur de l'élément)
  function zoneDist(z) {
    const l = zoneLink.get(z.id);
    if (!l) return { d: Math.hypot(W.pos.x - z.x, W.pos.z - z.z), dy: W.pos.y - z.y };
    const b = l.box, p = W.pos;
    return { d: Math.hypot(Math.max(b.min.x - p.x, 0, p.x - b.max.x), Math.max(b.min.z - p.z, 0, p.z - b.max.z)), dy: p.y < b.min.y ? p.y - b.min.y : (p.y > b.max.y ? p.y - b.max.y : 0) };
  }
  function zoneTick() {
    if (!zones.length) return;
    let best = null, bd = 1e9;
    for (const z of zones) {
      if (z.type === 'spawn' || zoneOff(z)) continue;
      const { d, dy } = zoneDist(z);
      if (z.type === 'portal' && z.trigger !== 'click') {
        const inside = d <= z.radius && dy > -1.5 && dy < 3.5, was = zoneInside.has(z.id);
        if (inside && !was) { zoneInside.add(z.id); fireZone(z, 'enter'); }
        else if (!inside && was) zoneInside.delete(z.id);
      }
      if (z.trigger !== 'enter') {
        const reach = zoneLink.has(z.id) ? z.radius : (z.shape === 'board' ? Math.max(z.radius, 2) : z.radius) + 1.5;
        if (d <= reach && Math.abs(dy) < 3.5 && d < bd) { best = z; bd = d; }
      }
    }
    if (best !== nearZone) { nearZone = best; if (onNear) onNear(best); }
  }
  // v36 : E déclenche la zone proche (déclenchement « clic » ou « both »), comme avant la v35 ; E ne fait rien d'autre
  window.addEventListener('keydown', e => {
    if (e.code === 'KeyE' && !e.repeat && walking && !typing(e) && !e.ctrlKey && !e.metaKey && !e.altKey && nearZone && onZone) fireZone(nearZone, 'key');
  });
  // ---- repère d'atterrissage : un cercle posé sur le sol, sous la cible de la vue globale (où F pose l'avatar)
  let onLanding = null, landY = null, landKey = '', landT = 0, landDirty = false;
  const UPV = new THREE.Vector3(0, 1, 0), landN = new THREE.Vector3(0, 1, 0);
  function faceUp(h, out) {
    out.copy(UPV);
    if (h.face) { const n = h.face.normal.clone().transformDirection(h.object.matrixWorld); if (n.y < 0) n.negate(); if (n.y > 0.6) out.copy(n); }
  }
  const landing = new THREE.Group(); landing.visible = false; scene.add(landing);
  {
    const bm = o => Object.assign({ transparent: true, opacity: 0.85, depthTest: true, depthWrite: false, fog: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }, o);
    const ro = new THREE.Mesh(new THREE.RingGeometry(0.75, 0.9, 40), new THREE.MeshBasicMaterial(bm({ color: 0x000000 })));
    ro.rotation.x = -Math.PI / 2; ro.position.y = 0.06; landing.add(ro);
    const ri = new THREE.Mesh(new THREE.RingGeometry(0.6, 0.75, 40), new THREE.MeshBasicMaterial(bm({ color: 0xffffff })));
    ri.rotation.x = -Math.PI / 2; ri.position.y = 0.065; landing.add(ri);
  }
  const downRay = new THREE.Raycaster(), DOWN = new THREE.Vector3(0, -1, 0);
  function solidHit(h, tokens) {
    const o = h.object;
    if (!o.isMesh || !o.visible) return false;
    const m = Array.isArray(o.material) ? o.material[h.face ? h.face.materialIndex : 0] : o.material;
    if (m && (isFoliageName(m.name) || nameHas(m.name, tokens))) return false;
    return !isIgnoredMesh(o, tokens);
  }
  // même règle que l'atterrissage : surface la plus haute à moins de 2 m au-dessus de la cible, sinon la plus haute du modèle
  function groundUnder(t) {
    if (!model) return null;
    const tokens = parseIgnore(cfg.walkIgnore);
    for (const oy of [t.y + 2, 1e5]) {
      downRay.set(new THREE.Vector3(t.x, oy, t.z), DOWN);
      for (const h of downRay.intersectObject(model, true)) if (solidHit(h, tokens)) { faceUp(h, landN); return h.point.y; }
    }
    return null;
  }
  const tkey = t => t.x.toFixed(2) + ',' + t.y.toFixed(2) + ',' + t.z.toFixed(2);
  function landingTick(now) {
    const show = !!model && !walking && cfg.landingMarker !== false;
    if (landing.visible !== show) { landing.visible = show; dirty = true; }
    if (!show) return;
    const t = controls.target, k = tkey(t);
    if (k !== landKey) { landKey = k; landT = now; landDirty = true; }
    if (landDirty && now - landT > 120) { landDirty = false; landY = groundUnder(t); dirty = true; }
    landing.position.set(t.x, landY === null ? t.y : landY, t.z);
    landing.quaternion.setFromUnitVectors(UPV, landN);
    landing.scale.setScalar(Math.max(1, camera.position.distanceTo(t) / 60));
  }
  function setLanding(e) {
    if (!model) return false;
    const r = dom.getBoundingClientRect();
    camera.updateMatrixWorld(true);
    tpV.set((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); tpRay.setFromCamera(tpV, camera);
    const tokens = parseIgnore(cfg.walkIgnore);
    for (const h of tpRay.intersectObject(model, true)) {
      if (!solidHit(h, tokens)) continue;
      controls.target.copy(h.point); controls.update(); dirty = true;
      landY = h.point.y; landKey = tkey(controls.target); landDirty = false; faceUp(h, landN);
      if (onLanding) onLanding(h.point.toArray());
      return true;
    }
    // mode tuiles : la vue d'ensemble sert à désigner un point lointain (la cible suit, les tuiles se chargent) ; le sol réel est repris dès que la tuile est prête
    if (OV.root) for (const h of tpRay.intersectObjects(ovCells(), true)) {
      if (!h.object.isMesh) continue;
      controls.target.copy(h.point); controls.update(); dirty = true;
      landY = h.point.y; landKey = tkey(controls.target); landDirty = false; faceUp(h, landN);
      if (onLanding) onLanding(h.point.toArray());
      return true;
    }
    return false;
  }

  const clock = new THREE.Clock();
  const RS = { times: [], last: 0 };   // v42 : instants des derniers rendus (diagnostic), plafond d'images par seconde (cfg.fpsMax, 0 = sans limite)
  function renderStats() {
    const now = performance.now(), causes = [];
    if (seaMat && seaMat.uniforms) causes.push('sea');
    if (P.peers.size) causes.push('peers');
    if (walking) causes.push('walk');
    if (TL.on && (TL.inflight > 0 || TL.gridQ.length)) causes.push('tiles');
    return { rate: RS.times.filter(t => now - t <= 5000).length / 5, causes };
  }
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.1);
    let moved = false;
    if (walking) { walkStep(dt); moved = true; } else moved = controls.update();
    if (TL.on) tilesTick(performance.now());
    presenceTick(dt, performance.now());
    landingTick(performance.now());
    if (seaMat && seaMat.uniforms) { seaMat.uniforms.uTime.value = clock.elapsedTime; dirty = true; }
    if (dirty || moved) {
      const now = performance.now(), fm = Number(cfg.fpsMax);
      if (fm > 0 && now - RS.last < 1000 / fm - 2) { dirty = true; return; }   // plafond atteint : l'image attend le tour suivant
      RS.last = now; RS.times.push(now); if (RS.times.length > 400) RS.times.splice(0, RS.times.length - 400);
      if (zoneLabs.length) coneScaleTick(); renderer.render(scene, camera); dirty = false;
    }
  });

  return {
    scene, camera, renderer, controls, cfg, setCfg, setModel, loadBuffer, frame, getCameraState, setZoom, renderStats,
    get model() { return model; }, get sea() { return sea; }, set onCfg(f) { onCfg = f; }, set onWalk(f) { onWalk = f; }, set onPick(f) { onPick = f; }, set pickOrbit(v) { pickOrbit = !!v; }, set onPresence(f) { onPresence = f; }, set onChat(f) { onChat = f; }, set onPeer(f) { onPeer = f; },
    setZones, zoneSelect, zonePickAt, findMeshes,
    // v36 : repères de portail (cônes) : affichés ou non (T), rappel, état pour les tests
    setCones, get cones() { return coneOn; }, set onCones(f) { onCones = f; },
    getCones() { const out = []; zoneGroup.traverse(o => { if (o.userData && o.userData.cone) { const p = o.getWorldPosition(new THREE.Vector3()); camera.updateMatrixWorld(true); const r = dom.getBoundingClientRect(), pr = p.clone().project(camera), d = camera.position.distanceTo(p); out.push({ id: o.userData.zone.id, visible: o.visible, pos: p.toArray(), scale: o.scale.x, dist: d, sx: r.left + (pr.x + 1) / 2 * r.width, sy: r.top + (1 - pr.y) / 2 * r.height, px: 0.35 * o.scale.x / (2 * d * Math.tan(camera.fov * Math.PI / 360)) * r.height }); } }); return out; },
    // mode tuiles (cfg.tiles) : voir loadTiles ; tilesState sert aux tests
    closeTiles, releaseAnchor, get seaCenter() { return [seaCx, seaCz]; },
    // v32 : le point visé (rayon THREE.Raycaster) sur la vue d'ensemble, hors tuiles chargées ; null si rien
    overviewHit(ray) { for (const h of ray.intersectObjects(ovCells(), true)) if (h.object.isMesh) return h.point.toArray(); return null; },
    // v32 : demande le chargement des tuiles autour de (x, z) pendant 15 s ; rend les fichiers des tuiles qui contiennent ce point
    tilesForce(x, z) { TL.forced = { x, z }; TL.forcedUntil = performance.now() + 15000; tilesUpdate(performance.now()); return TL.tiles.filter(t => inTile(t, x, z, TILE_M)).map(t => t.file); },
    // v32 : état des zones telles que la scène les montre (tests, diagnostic)
    getZoneState() {
      return zones.map(z => {
        const l = zoneLink.get(z.id), g = zoneGroup.children.find(c => c.userData.zoneId === z.id), off = zoneOff(z);
        return { id: z.id, type: z.type, mesh: z.mesh || '', linked: !!l, off, shown: !off, box: l ? l.box.min.toArray().concat(l.box.max.toArray()) : null,
          pos: l ? [(l.box.min.x + l.box.max.x) / 2, l.box.min.y, (l.box.min.z + l.box.max.z) / 2] : (g ? g.position.toArray() : [z.x, z.y, z.z]) };
      });
    },
    // v33 : marqueurs dessinés pour chaque zone (tests, diagnostic) : types (disc, ring, range, spawn) et rayon de l'anneau de portée
    getMarkers() {
      return zoneGroup.children.map(g => { const k = []; let radius = null; g.traverse(o => { if (o.userData && o.userData.marker) { k.push(o.userData.marker); if (o.userData.radius) radius = o.userData.radius; } }); return { id: g.userData.zoneId, kinds: k, radius }; });
    },
    loadTiles, tilesState, get tiled() { return TL.on; }, set onTiles(f) { TL.onInfo = f; }, set onTileError(f) { TL.onError = f; },
    // référence (champ mesh d'une zone) de cet objet du modèle : nom, ou nom#index si le nom est partagé
    meshRef(o) {
      if (TL.on && TL.root) { for (let p = o; p && p !== TL.root; p = p.parent) if (p.userData && typeof p.userData.ref === 'string') return p.userData.ref; return ''; }
      return model ? meshRefOf(model, o) : (o.name || '');
    }, get rotation() { return modelRot; },
    // boîte (monde) de l'élément de ce nom : { min, max, center, count } ou null
    meshInfo(name) { const m = findMeshes(name); const b = m.length ? refBox(name, m) : null; if (!b) return null; return { min: b.min.toArray(), max: b.max.toArray(), center: b.getCenter(new THREE.Vector3()).toArray(), size: b.getSize(new THREE.Vector3()).toArray(), count: m.length }; },
    set linkMode(v) { linkLock = !!v; },
    isTraversable(o) { return isIgnoredMesh(o, parseIgnore(cfg.walkIgnore)); }, getZones() { return zones.map(z => Object.assign({}, z)); }, set onZone(f) { onZone = f; }, set onNear(f) { onNear = f; },
    captureTop(size = 320, hide = []) {
      if (!model) return null;
      const box = new THREE.Box3().setFromObject(model), c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3());
      const h = (Math.max(sz.x, sz.z) * 0.53) || 50, cv = renderer.domElement, W = cv.width, H = cv.height, a = W / H;
      const cam = new THREE.OrthographicCamera(-h * a, h * a, h, -h, 1, (box.max.y - box.min.y) + 3000);
      cam.position.set(c.x, box.max.y + 500, c.z); cam.up.set(0, 0, -1); cam.lookAt(c.x, 0, c.z);
      cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);
      const hidden = [];
      for (const o of [landing, zoneGroup, hoverG, selfAv, ...hide, ...[...P.peers.values()].map(q => q.g)]) if (o && o.visible) { o.visible = false; hidden.push(o); }
      const fog = scene.fog; scene.fog = null;
      renderer.render(scene, cam);
      const out = document.createElement('canvas'); out.width = out.height = size;
      const s = Math.min(W, H);
      out.getContext('2d').drawImage(cv, (W - s) / 2, (H - s) / 2, s, s, 0, 0, size, size);
      const url = out.toDataURL('image/jpeg', 0.82);
      scene.fog = fog; hidden.forEach(o => { o.visible = true; }); dirty = true;
      return url;
    },
    getName() { return P.name; }, set onLanding(f) { onLanding = f; }, set onName(f) { onName = f; },
    spectate(on) { spectateOn = !!on; if (spectateOn) { if (cfg.presenceUrl && !P.ws) presenceConnect(); } else if (!walking) presenceDisconnect(); },
    // v37 : demande les n messages précédant le message numéro `before` ; un ancien serveur ne répond pas (la page masque alors le bouton)
    requestHistory(before, n) { if (!P.ws || P.ws.readyState !== 1 || !P.id || !Number.isFinite(before)) return false; P.ws.send(JSON.stringify({ t: 'history', before, n: n || 50 })); return true; },
    set onHistory(f) { onHistory = f; },
    sendChat(text) {
      const t = String(text || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, 200);
      if (!t || !P.ws || P.ws.readyState !== 1 || !P.id) return false;
      P.ws.send(JSON.stringify({ t: 'chat', text: t })); return true;
    },
    releaseKeys() { W.keys.clear(); },
    // v33 : touches fléchées tenues depuis la saisie du chat (les lettres vont dans le texte, les flèches déplacent l'avatar)
    holdKey(code, on) { if (!walking || !code.startsWith('Arrow')) return; if (on) W.keys.add(code); else W.keys.delete(code); },
    // v46 : flèches à l'écran : touche tenue (avancer, reculer, tourner, monter, descendre), saut, course allumée par un clic, vue globale pas à pas
    padKey(code, on) { if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'KeyA', 'KeyD', 'PageUp', 'PageDown'].includes(code)) return false; if (!walking) { W.keys.delete(code); return false; } if (on) W.keys.add(code); else W.keys.delete(code); return true; },
    padJump() { if (!walking || W.fly || W.view === 'free') return false; W.jumpReq = true; return true; },
    get runLatch() { return !!W.runLatch && walking; }, set runLatch(v) { W.runLatch = !!v && walking; if (onView) onView(); },
    globalMove, globalTurn, globalZoom,
    // v33 : point de retour ({ pos, yaw, forF }), aller à, retour, vol, vues, couleur choisie, clignotement de bulle
    setHome(h) { home = h && Array.isArray(h.pos) && h.pos.length >= 3 && h.pos.every(Number.isFinite) ? { pos: h.pos.slice(0, 3), yaw: Number.isFinite(h.yaw) ? h.yaw : undefined, forF: !!h.forF } : null; },
    get home() { return home; }, goTo, returnHome, toggleFly, cycleView, setView,
    set onMouse(f) { onMouse = f; }, grabMouse, get mouseState() { return mouseState(); }, set onView(f) { onView = f; }, set onFly(f) { onFly = f; }, tickPresence(dt, now) { presenceTick(dt, now); },   // tickPresence : pas de présence à la main, pour les tests (bulle qui clignote)
    get viewName() { return VIEW_NAMES[W.view]; }, get view() { return W.view; }, get flying() { return W.fly; }, getHeading() {   // v37 : cap en degrés (0 = nord, sens horaire). Nord d'OpenSim = -Z du modèle ; + rotation de la région + cfg.northDeg
      let psi;
      if (walking) psi = W.yaw;
      else { const d = camera.getWorldDirection(new THREE.Vector3()); if (Math.hypot(d.x, d.z) < 1e-4) return null; psi = Math.atan2(-d.x, -d.z); }
      const deg = rotDeg() - psi * 180 / Math.PI + (Number(cfg.northDeg) || 0);
      return ((deg % 360) + 360) % 360;
    },
    get running() { return !!W.runOn && walking; },
    // v34 : la couleur choisie est envoyée au serveur aussitôt si la connexion est ouverte (sinon dans « hello ») ; l'avatar du visiteur la prend
    setMyColor(c) {
      P.myColor = Number.isInteger(c) && c >= 0 && c <= 0xFFFFFF ? c : null;
      pushColor();
      if (walking) updateSelf();
    },
    // v34 : clé d'identité du navigateur (lien personnel) : lecture, remplacement (la connexion est refaite pour que le serveur reconnaisse la clé)
    getUid() { return uid; },
    setUid(k) {
      if (!/^[0-9a-f]{32}$/.test(String(k))) return false;
      uid = String(k); try { localStorage.setItem('glb2html_uid', uid); } catch (_) {}
      if (P.ws) { const ws = P.ws; P.ws = null; P.id = null; try { ws.close(); } catch (_) {} clearPeers(); if (walking || spectateOn) presenceConnect(); }
      return true;
    },
    blinkBubble: blinkStart, blinkStop, get blinking() { return BL.on; }, set onBlink(f) { onBlink = f; }, set onBlinkEnd(f) { onBlinkEnd = f; },
    setName(n) { P.name = cleanName(n); if (P.ws && P.ws.readyState === 1) P.ws.send(JSON.stringify({ t: 'name', name: P.name })); },
    getPresence() { return { state: P.state, id: P.id, opened: P.opened, stopped: P.stopped, tries: P.retry, closeCode: P.closeCode, closeReason: P.closeReason, peers: [...P.peers.values()].map(q => ({ id: q.id, name: q.name, pos: q.g.position.toArray(), visible: q.g.visible, bubble: !!q.bubble, bubbleVisible: !!q.bubble && q.bubble.visible, labelVisible: (q.g.children.find(o => o.isSprite && !o.userData.isBubble) || { visible: null }).visible, blinking: !!q.blink, blinkHidden: q.blinkHidden || 0, color: q.color, stack: avatarStack(q) })) }; }, get walking() { return walking; },
    walkTick(dt) { if (walking) walkStep(dt); },
    refreshCollision() { if (TL.on) { for (const t of TL.tiles) if (t.state === 'ready' && t.grp) { t.state = 'building'; t.grid = null; t.gen = collisionGridSteps(t.grp, 3, parseIgnore(cfg.walkIgnore)); t.qAt = performance.now(); t.qFirst = true; t.gridCpu = 0; TL.gridQ.push(t); } } else if (walking && model) W.grid = buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore)); },
    teleportNdc(nx, ny) { return walkTeleport(nx, ny); },
    toggleWalk, pressF, recenterCam, startFly, walkStart, walkStop, teleportTo,
    getWalk() { return { pos: W.pos.toArray(), yaw: W.yaw, pitch: W.pitch, grounded: W.grounded, tris: W.grid ? W.grid.count : 0, flying: W.fly, view: W.view, camYaw: W.view === 'tps' ? W.tyaw : (W.view === 'free' ? W.cyaw : W.yaw), tpsDist: W.tdist, camPitch: W.view === 'tps' ? W.tpitch : (W.view === 'free' ? W.cpitch : W.pitch), running: W.run.size > 0 || W.keys.has('ShiftLeft') || W.keys.has('ShiftRight') || !!W.runLatch, cam: camera.position.toArray(), selfVisible: !!(selfAv && selfAv.visible) }; }, get fit() { return fit; }, requestRender() { dirty = true; }
  };
}
