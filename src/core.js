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
function parseIgnore(s) { return String(s || '').toLowerCase().split(/[,;]+/).map(x => x.trim()).filter(Boolean); }

function describeObject(o) {
  const sz = new THREE.Box3().setFromObject(o).getSize(new THREE.Vector3());
  const parents = []; for (let q = o.parent; q; q = q.parent) if (q.name) parents.push(q.name);
  const mats = (Array.isArray(o.material) ? o.material : [o.material]).map(m => m && m.name).filter(Boolean);
  const token = o.name || parents[0] || mats[0] || '';
  return {
    name: token, mesh: o.name || '', parents, materials: mats, token, size: sz.toArray(),
    text: 'mesh : ' + (o.name || '(sans nom)') + '\nparents : ' + (parents.slice(0, 3).join(' › ') || '(aucun)') + '\nmatériau : ' + (mats.join(', ') || '(sans nom)') + '\ntaille (m) : ' + sz.toArray().map(v => v.toFixed(2)).join(' × ')
  };
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

// Grille XZ de triangles (monde) pour sol et murs : exclut le feuillage
function buildCollisionGrid(root, cell = 3, tokens = []) {
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
      for (let k = 0; k < 3; k++) {
        v.fromBufferAttribute(p, ix ? ix.getX(i * 3 + k) : i * 3 + k).applyMatrix4(M);
        T[t * 9 + k * 3] = v.x; T[t * 9 + k * 3 + 1] = v.y; T[t * 9 + k * 3 + 2] = v.z;
      }
    }
  }
  const cells = new Map(), big = [];
  const key = (ix, iz) => (ix + 32768) * 65536 + (iz + 32768);
  for (let i = 0; i < total; i++) {
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

function createViewer(container, cfg0, loader) {
  const cfg = Object.assign({}, cfg0);
  let onCfg = null, onWalk = null, onPick = null, onPresence = null, onChat = null, onName = null, spectateOn = false, pickOrbit = false, walking = false;
  const W = { pos: new THREE.Vector3(), spawn: new THREE.Vector3(), vy: 0, grounded: true, yaw: 0, pitch: 0, keys: new Set(), jumpReq: false, drag: false, saved: null, grid: null };
  let model = null, fit = 1, sea = null, seaMat = null, dirty = true, foliageMats = [];

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(cfg.skyColor);
  scene.fog = new THREE.Fog(cfg.skyColor, 1500, 4500);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 5000);
  camera.position.set(0, 22, 45);

  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
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
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.addEventListener('change', () => { dirty = true; });

  scene.add(new THREE.AmbientLight(0xffffff, 1.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.8); sun.position.set(120, 200, 80); scene.add(sun);
  const sun2 = new THREE.DirectionalLight(0xffffff, 0.7); sun2.position.set(-80, 100, -120); scene.add(sun2);
  const hemi = new THREE.HemisphereLight(cfg.skyColor, 0xffe8b0, 0.8); scene.add(hemi);

  function resize() {
    const w = container.clientWidth || innerWidth, h = container.clientHeight || innerHeight;
    renderer.setPixelRatio(cfg.retina ? Math.min(Math.max(window.devicePixelRatio || 1, 2), 3) : 1);
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
      sea.position.y = cfg.seaY;
      sea.frustumCulled = false;
      sea.renderOrder = -10;
      sea.userData.isSea = true;
      scene.add(sea);
    }
    dirty = true;
  }
  buildSea();

  function fixMaterials(root) {
    foliageMats = [];
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
    if (model) { scene.remove(model); disposeObject(model); }
    model = root;
    fixMaterials(root);
    // centre = moyenne des origines de meshes, puis y+15
    const sum = new THREE.Vector3(), wp = new THREE.Vector3(); let cnt = 0;
    root.traverse(o => { if (o.isMesh) { o.getWorldPosition(wp); sum.add(wp); cnt++; } });
    const center = cnt ? sum.divideScalar(cnt) : new THREE.Box3().setFromObject(root).getCenter(new THREE.Vector3());
    root.position.sub(center); root.position.y += 15;
    root.updateMatrixWorld(true);
    root.traverse(o => { if (o.isMesh) { o.updateMatrix(); o.matrixAutoUpdate = false; } });
    scene.add(root);
    const size = new THREE.Box3().setFromObject(root).getSize(new THREE.Vector3());
    fit = Math.max(size.x, size.y, size.z) / 2 / Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) * 1.35 || 1;
    frame();
  }

  async function loadBuffer(buf) {
    const gltf = await loader.parseAsync(buf, '');
    setModel(gltf.scene);
    return gltf;
  }

  function setCfg(p) {
    Object.assign(cfg, p);
    if ('skyColor' in p) { scene.background.set(cfg.skyColor); scene.fog.color.set(cfg.skyColor); hemi.color.set(cfg.skyColor); }
    if ('retina' in p) resize();
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
    if (sea) sea.position.y = cfg.seaY;
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
  function walkStep(dt) {
    const k = W.keys;
    const run = k.has('ShiftLeft') || k.has('ShiftRight');
    if (k.has('ArrowLeft')) W.yaw += 1.8 * dt;
    if (k.has('ArrowRight')) W.yaw -= 1.8 * dt;
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const s = (k.has('KeyD') ? 1 : 0) - (k.has('KeyA') ? 1 : 0);
    const sy = Math.sin(W.yaw), cy = Math.cos(W.yaw);
    let mx = -sy * f + cy * s, mz = -cy * f - sy * s;
    const len = Math.hypot(mx, mz);
    const G = W.grid, hasGround = G && G.count > 0;
    if (len > 0 && dt > 0) {
      mx /= len; mz /= len;
      const dist = cfg.walkSpeed * (run ? 2.2 : 1) * dt;
      let dx = mx * dist, dz = mz * dist;
      if (hasGround) {
        const hit = G.wall(W.pos.x, W.pos.y + 0.9, W.pos.z, mx, mz, dist + 0.35);
        if (hit) {
          let nx = hit.nx, nz = hit.nz; const nl = Math.hypot(nx, nz) || 1; nx /= nl; nz /= nl;
          if (nx * mx + nz * mz > 0) { nx = -nx; nz = -nz; }
          const d = dx * nx + dz * nz; dx -= d * nx; dz -= d * nz;
        }
        if (G.ground(W.pos.x + dx, W.pos.z + dz, W.pos.y + STEP_UP) !== null) { W.pos.x += dx; W.pos.z += dz; }
      } else { W.pos.x += dx; W.pos.z += dz; }
    }
    if ((W.jumpReq || k.has('Space')) && W.grounded) { W.vy = 5.5; W.grounded = false; W.pos.y += 0.02; }
    W.jumpReq = false;
    const g = hasGround ? G.ground(W.pos.x, W.pos.z, W.pos.y + STEP_UP) : null;
    if (W.grounded) {
      if (g !== null) {
        if (W.pos.y - g > 0.6) W.grounded = false;
        else W.pos.y += (g - W.pos.y) * Math.min(1, dt * 18);
      }
    }
    if (!W.grounded) {
      W.vy -= 15 * dt; W.pos.y += W.vy * dt;
      if (g !== null && W.pos.y <= g) { W.pos.y = g; W.vy = 0; W.grounded = true; }
      if (W.pos.y < W.spawn.y - 400) { W.pos.copy(W.spawn); W.vy = 0; W.grounded = true; }
    }
    camera.position.set(W.pos.x, W.pos.y + cfg.eyeHeight, W.pos.z);
    camera.rotation.set(W.pitch, W.yaw, 0);
    if (dt > 0) zoneTick();
  }
  function walkStart(opts) {
    if (!model || walking) return walking;
    W.grid = buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore));
    W.saved = { pos: camera.position.clone(), target: controls.target.clone(), fov: camera.fov };
    const t = (opts && opts.pos) ? new THREE.Vector3().fromArray(opts.pos) : controls.target, fx = t.x - camera.position.x, fz = t.z - camera.position.z;
    W.yaw = (opts && Number.isFinite(opts.yaw)) ? opts.yaw : (Math.hypot(fx, fz) > 1e-3 ? Math.atan2(-fx, -fz) : 0);
    W.pitch = 0;
    let g = W.grid.ground(t.x, t.z, t.y + 2);
    if (g === null) g = W.grid.ground(t.x, t.z, 1e6);
    W.pos.set(t.x, g === null ? t.y : g, t.z); W.spawn.copy(W.pos);
    W.vy = 0; W.grounded = true; W.keys.clear(); W.drag = false;
    controls.enabled = false;
    camera.fov = 70; camera.updateProjectionMatrix();
    camera.rotation.order = 'YXZ';
    walking = true;
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
    zoneInside.clear(); nearZone = null;
    for (const z of zones) if (z.type === 'portal' && z.trigger !== 'click' && Math.hypot(W.pos.x - z.x, W.pos.z - z.z) <= z.radius) zoneInside.add(z.id);
    walkStep(0); dirty = true;
    presenceEnter();
    if (onWalk) onWalk(true);
    return true;
  }
  function walkStop() {
    if (!walking) return;
    walking = false; W.keys.clear(); W.drag = false;
    if (document.pointerLockElement === dom && document.exitPointerLock) document.exitPointerLock();
    camera.rotation.order = 'XYZ';
    camera.fov = W.saved.fov; camera.updateProjectionMatrix();
    camera.position.copy(W.saved.pos); controls.target.copy(W.saved.target);
    controls.enabled = true; controls.update();
    W.grid = null; dirty = true;
    zoneInside.clear(); if (nearZone) { nearZone = null; if (onNear) onNear(null); }
    presenceLeave();
    if (onWalk) onWalk(false);
  }
  const typing = e => { const n = e.target && e.target.tagName; return n === 'INPUT' || n === 'TEXTAREA' || n === 'SELECT'; };
  const MOVE_KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'ShiftLeft', 'ShiftRight']);
  window.addEventListener('keydown', e => { if (!walking || typing(e) || !MOVE_KEYS.has(e.code)) return; W.keys.add(e.code); if (e.code === 'Space') W.jumpReq = true; e.preventDefault(); });
  window.addEventListener('keyup', e => { W.keys.delete(e.code); });
  window.addEventListener('blur', () => W.keys.clear());
  dom.addEventListener('mousedown', () => { if (walking) W.drag = true; });
  window.addEventListener('mouseup', () => { W.drag = false; });
  window.addEventListener('mousemove', e => {
    if (!walking || !(W.drag || document.pointerLockElement === dom)) return;
    W.yaw -= (e.movementX || 0) * 0.0022;
    W.pitch = Math.max(-1.45, Math.min(1.45, W.pitch - (e.movementY || 0) * 0.0022));
  });
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
    for (const h of tpRay.intersectObject(model, true)) if (h.object.isMesh && h.object.visible) return Object.assign(describeObject(h.object), { point: h.point.toArray() });
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
    const locked = document.pointerLockElement === dom, now = performance.now();
    {
      const rc = dom.getBoundingClientRect();
      const cnx = locked ? 0 : (e.clientX - rc.left) / rc.width * 2 - 1, cny = locked ? 0 : -((e.clientY - rc.top) / rc.height) * 2 + 1;
      const still = !!downPos && Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]) < 6;
      if (zones.length && onZone && (walking || (still && !zoneEditor))) {
        const zc = zoneFromClick(cnx, cny, walking ? 14 : 0);
        if (zc) { fireZone(zc, 'click'); return; }
      }
    }
    if (!walking) {
      if (pickOrbit && onPick && downPos && Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]) < 6) doPick(e, false);
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
    try { const p = dom.requestPointerLock(); if (p && p.catch) p.catch(() => {}); } catch (_) {}
    doPick(e, locked);
  });

  // ---- présence : autres visiteurs (WebSocket)
  const uid = (() => {
    let u = ''; try { u = localStorage.getItem('glb2html_uid') || ''; } catch (_) {}
    if (u.length < 16) {
      const a = new Uint8Array(16);
      if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(a); else for (let i = 0; i < 16; i++) a[i] = Math.random() * 256;
      u = [...a].map(b => b.toString(16).padStart(2, '0')).join('');
      try { localStorage.setItem('glb2html_uid', u); } catch (_) {}
    }
    return u;
  })();
  const P = { ws: null, id: null, peers: new Map(), last: 0, name: '', state: 'off', retry: 0, timer: 0, sent: [0, 0, 0, 0] };
  const r2 = v => Math.round(v * 100) / 100;
  const cleanName = s => String(s || '').replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 24);
  function pStatus(state) { P.state = state; if (onPresence) onPresence({ state, count: state === 'online' ? P.peers.size + (walking ? 1 : 0) : 0, spectator: !walking }); }
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
    body.position.y = 0.69; g.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf0c8a0, roughness: 0.8 }));
    head.position.y = 1.56; g.add(head);
    const nose = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 8), new THREE.MeshStandardMaterial({ color: 0x333333 }));
    nose.rotation.x = -Math.PI / 2; nose.position.set(0, 1.56, -0.2); g.add(nose);
    const label = makeLabel(name); label.position.y = 2.1; g.add(label);
    const beacon = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.8, 10), new THREE.MeshBasicMaterial({ color: 0x000000, depthTest: false, transparent: true, fog: false }));
    beacon.rotation.x = Math.PI; beacon.position.y = 3.0; beacon.visible = false; g.add(beacon);
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
    sp.position.y = 2.4 + h * 0.0025;
    sp.userData.isBubble = true;
    return sp;
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
  function removePeer(id) { const q = P.peers.get(id); if (q) { disposeAvatar(q.g); P.peers.delete(id); } }
  function clearPeers() { for (const id of [...P.peers.keys()]) removePeer(id); }
  function presenceMsg(m) {
    if (!m || typeof m !== 'object') return;
    if (m.t === 'welcome') {
      P.id = m.id; (m.peers || []).forEach(addPeer); pStatus('online');
      if (m.name) setMyName(m.name);
      if (m.role === 'spectator' && walking && P.ws) P.ws.send(JSON.stringify({ t: 'role', walker: true, name: P.name }));
      if (onChat && cfg.chat !== false) (m.history || []).forEach(h => onChat({ id: h.id, name: cleanName(h.name) || '?', text: String(h.text || '').slice(0, 200), self: false, history: true }));
    }
    else if (m.t === 'join') { addPeer(m); pStatus('online'); if (onChat && cfg.chat !== false) onChat({ system: true, text: (cleanName(m.name) || '?') + ' a rejoint' }); }
    else if (m.t === 'leave') { const q = P.peers.get(m.id); removePeer(m.id); pStatus('online'); if (q && onChat && cfg.chat !== false) onChat({ system: true, text: q.name + ' est parti' }); }
    else if (m.t === 'chat' && cfg.chat !== false) {
      const text = String(m.text || '').slice(0, 200), q = P.peers.get(m.id);
      if (q) showBubble(q, text);
      if (onChat) onChat({ id: m.id, name: cleanName(m.name) || (q && q.name) || '?', text, self: m.id === P.id, history: false });
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
    else if (m.t === 'full') { pStatus('full'); }
    dirty = true;
  }
  function presenceConnect() {
    if (!cfg.presenceUrl || P.ws) return;
    pStatus('connecting');
    let ws;
    try { ws = new WebSocket(String(cfg.presenceUrl).trim().replace(/^(wss?:\/\/)0\.0\.0\.0(?=[:/]|$)/i, (m, p) => p + '127.0.0.1')); } catch (_) { pStatus('error'); return; }
    P.ws = ws;
    ws.onopen = () => { P.retry = 0; ws.send(JSON.stringify({ t: 'hello', room: cfg.room || cfg.roomDefault || '', name: P.name, uid, spectator: !walking })); };
    ws.onmessage = ev => { let m; try { m = JSON.parse(ev.data); } catch (_) { return; } presenceMsg(m); };
    ws.onerror = () => {};
    ws.onclose = () => {
      if (P.ws !== ws) return;
      P.ws = null; P.id = null; clearPeers();
      if ((walking || spectateOn) && P.state !== 'full') { pStatus('error'); clearTimeout(P.timer); P.timer = setTimeout(presenceConnect, Math.min(15000, 1500 * (++P.retry))); }
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
  function presenceTick(dt, now) {
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
        if (lab) { lab.scale.set(1.6 * k, 0.4 * k, 1); lab.position.y = 2.1 + 0.55 * (k - 1); }
        if (bc) { bc.visible = dist > 14; bc.scale.setScalar(k); bc.position.y = 3.0 + 0.9 * (k - 1); }
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
  let zones = [], zoneHit = [], zoneAll = [], zoneInside = new Set(), nearZone = null, zoneEditor = false, selBox = null, onZone = null, onNear = null;
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
      target: String(z.target || '').slice(0, 600), spawn: slug(z.spawn), confirm: !!z.confirm, private: !!z.private
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
  function buildZones() {
    for (const c of [...zoneGroup.children]) {
      zoneGroup.remove(c);
      c.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
    }
    if (selBox) { scene.remove(selBox); selBox.geometry.dispose(); selBox.material.dispose(); selBox = null; }
    zoneHit = []; zoneAll = [];
    for (const z of zones) {
      const g = new THREE.Group(); g.position.set(z.x, z.y, z.z); g.rotation.y = z.yaw; g.userData.zoneId = z.id;
      const kind = { url: 'Lien web', ha: 'Commande', portal: 'Portail', spawn: 'Arrivée' }[z.type];
      const priv = zoneEditor && z.private ? ' (privé)' : '';
      const clickable = z.type !== 'spawn' && z.trigger !== 'enter';
      let main = null;
      if (z.type === 'spawn') {
        if (!zoneEditor) continue;
        const cone = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.9, 12), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, depthTest: false, fog: false }));
        cone.rotation.x = -Math.PI / 2; cone.position.y = 0.6; g.add(cone); main = cone;
        const l = makeLabel('arrivée : ' + z.id); l.position.y = 1.7; g.add(l);
      } else if (z.shape === 'board') {
        const sub = kind + (clickable ? ' · clic ou E' : '') + priv;
        const plane = new THREE.Mesh(new THREE.PlaneGeometry(z.w, z.h), new THREE.MeshBasicMaterial({ map: boardTex(z.label || kind, sub, z.w, z.h), side: THREE.DoubleSide, fog: false }));
        plane.position.y = 0.9 + z.h / 2; g.add(plane); main = plane;
        const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.92, 0.1), new THREE.MeshStandardMaterial({ color: 0x333333 })); post.position.y = 0.46; g.add(post);
      } else {
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(z.radius, z.radius, 2.4, 48, 1, true), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false, fog: false }));
        cyl.position.y = 1.2; g.add(cyl); main = cyl;
        const r1 = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.05, z.radius - 0.16), z.radius, 64), new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide, fog: false }));
        r1.rotation.x = -Math.PI / 2; r1.position.y = 0.05; g.add(r1);
        const r2 = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.02, z.radius - 0.3), Math.max(0.04, z.radius - 0.16), 64), new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: false }));
        r2.rotation.x = -Math.PI / 2; r2.position.y = 0.055; g.add(r2);
        const lab = makeLabel((z.label || kind) + priv); lab.position.y = 2.9; g.add(lab);
      }
      if (main) { main.userData.zone = z; zoneAll.push(main); if (clickable) zoneHit.push(main); }
      zoneGroup.add(g);
    }
    dirty = true;
  }
  function setZones(list, opts) {
    zoneEditor = !!(opts && opts.editor);
    const seen = new Set();
    zones = (Array.isArray(list) ? list : []).map((z, i) => cleanZone(z || {}, i)).map(z => {
      let id = z.id, n = 2; while (seen.has(id)) id = z.id + '-' + (n++);
      seen.add(id); z.id = id; return z;
    });
    nearZone = null; zoneInside.clear();
    buildZones();
    return zones.map(z => Object.assign({}, z));
  }
  function zoneSelect(id) {
    if (selBox) { scene.remove(selBox); selBox.geometry.dispose(); selBox.material.dispose(); selBox = null; }
    const g = zoneGroup.children.find(c => c.userData.zoneId === id);
    if (g) { selBox = new THREE.BoxHelper(g, 0x000000); selBox.material.depthTest = false; selBox.material.transparent = true; scene.add(selBox); }
    dirty = true;
  }
  function fireZone(z, how) {
    if (walking && P.ws && P.ws.readyState === 1 && P.id) P.ws.send(JSON.stringify({ t: 'zone', id: z.id, type: z.type, label: z.label }));
    if (onZone) onZone(z, how);
  }
  function zoneFromClick(nx, ny, maxDist) {
    if (!zoneHit.length) return null;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny); tpRay.setFromCamera(tpV, camera);
    const h = tpRay.intersectObjects(zoneHit, false)[0];
    if (!h || (maxDist && h.distance > maxDist)) return null;
    if (model) { const m = tpRay.intersectObject(model, true)[0]; if (m && m.distance < h.distance - 0.05) return null; }
    return h.object.userData.zone;
  }
  function zonePickAt(cx, cy) {
    if (!zoneAll.length) return null;
    const r = dom.getBoundingClientRect();
    camera.updateMatrixWorld(true);
    tpV.set((cx - r.left) / r.width * 2 - 1, -((cy - r.top) / r.height) * 2 + 1); tpRay.setFromCamera(tpV, camera);
    const h = tpRay.intersectObjects(zoneAll, false)[0];
    return h ? h.object.userData.zone : null;
  }
  function zoneTick() {
    if (!zones.length) return;
    let best = null, bd = 1e9;
    for (const z of zones) {
      if (z.type === 'spawn') continue;
      const d = Math.hypot(W.pos.x - z.x, W.pos.z - z.z), dy = W.pos.y - z.y;
      if (z.type === 'portal' && z.trigger !== 'click') {
        const inside = d <= z.radius && dy > -1.5 && dy < 3.5, was = zoneInside.has(z.id);
        if (inside && !was) { zoneInside.add(z.id); fireZone(z, 'enter'); }
        else if (!inside && was) zoneInside.delete(z.id);
      }
      if (z.trigger !== 'enter') {
        const reach = (z.shape === 'board' ? Math.max(z.radius, 2) : z.radius) + 1.5;
        if (d <= reach && Math.abs(dy) < 3.5 && d < bd) { best = z; bd = d; }
      }
    }
    if (best !== nearZone) { nearZone = best; if (onNear) onNear(best); }
  }
  window.addEventListener('keydown', e => {
    if (e.code === 'KeyE' && !e.repeat && walking && !typing(e) && nearZone && onZone) fireZone(nearZone, 'key');
  });

  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.1);
    let moved = false;
    if (walking) { walkStep(dt); moved = true; } else moved = controls.update();
    presenceTick(dt, performance.now());
    if (seaMat && seaMat.uniforms) { seaMat.uniforms.uTime.value = clock.elapsedTime; dirty = true; }
    if (dirty || moved) { renderer.render(scene, camera); dirty = false; }
  });

  return {
    scene, camera, renderer, controls, cfg, setCfg, setModel, loadBuffer, frame, getCameraState, setZoom,
    get model() { return model; }, get sea() { return sea; }, set onCfg(f) { onCfg = f; }, set onWalk(f) { onWalk = f; }, set onPick(f) { onPick = f; }, set pickOrbit(v) { pickOrbit = !!v; }, set onPresence(f) { onPresence = f; }, set onChat(f) { onChat = f; },
    setZones, zoneSelect, zonePickAt, getZones() { return zones.map(z => Object.assign({}, z)); }, set onZone(f) { onZone = f; }, set onNear(f) { onNear = f; },
    getName() { return P.name; }, set onName(f) { onName = f; },
    spectate(on) { spectateOn = !!on; if (spectateOn) { if (cfg.presenceUrl && !P.ws) presenceConnect(); } else if (!walking) presenceDisconnect(); },
    sendChat(text) {
      const t = String(text || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, 200);
      if (!t || !P.ws || P.ws.readyState !== 1 || !P.id) return false;
      P.ws.send(JSON.stringify({ t: 'chat', text: t })); return true;
    },
    releaseKeys() { W.keys.clear(); },
    setName(n) { P.name = cleanName(n); if (P.ws && P.ws.readyState === 1) P.ws.send(JSON.stringify({ t: 'name', name: P.name })); },
    getPresence() { return { state: P.state, id: P.id, peers: [...P.peers.values()].map(q => ({ id: q.id, name: q.name, pos: q.g.position.toArray(), visible: q.g.visible, bubble: !!q.bubble })) }; }, get walking() { return walking; },
    walkTick(dt) { if (walking) walkStep(dt); },
    refreshCollision() { if (walking && model) W.grid = buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore)); },
    teleportNdc(nx, ny) { return walkTeleport(nx, ny); },
    toggleWalk() { return walking ? walkStop() : walkStart(); }, walkStart, walkStop,
    getWalk() { return { pos: W.pos.toArray(), yaw: W.yaw, pitch: W.pitch, grounded: W.grounded, tris: W.grid ? W.grid.count : 0 }; }, get fit() { return fit; }, requestRender() { dirty = true; }
  };
}
