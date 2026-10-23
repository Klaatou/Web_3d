// ===== langue de la page (v36) =====
// Les textes sont dans src/i18n/<code>.json (un fichier par langue, clés stables, texte pur) ; build.py les intègre ici.
// Ajouter une langue = ajouter un fichier src/i18n/<code>.json (voir docs/fr/MANUEL.md § 21.9) : aucun code à toucher.
// Texte manquant dans une langue : anglais, puis français, puis la clé elle-même.
const I18N = __I18N_DATA__;
const I18N_LANGS = Object.keys(I18N).sort();
const I18N_KEY = 'glb2html_lang';
// v37 : paramètres après # ; le séparateur est & et # est accepté aussi (#name=A&lang=en = #name=A#lang=en). Fonction commune à tous les lecteurs du hash.
const hashParams = h => new URLSearchParams(String(h === undefined ? location.hash : h).replace(/^#/, '').replace(/#/g, '&'));
const i18nName = code => (I18N[code] && I18N[code]._name) || code;
const i18nMatch = tag => { const c = String(tag || '').toLowerCase().split(/[-_]/)[0]; return I18N[c] ? c : null; };
// choix de l'utilisateur : 'auto' ou un code de langue disponible. #lang=xx dans l'adresse est prioritaire et mémorisé.
const LANG_PREF = (() => {
  let pref = 'auto';
  try { const s = localStorage.getItem(I18N_KEY); if (s === 'auto' || I18N[s]) pref = s; } catch (_) {}
  try {
    const h = hashParams().get('lang');
    if (h !== null) { const v = h.toLowerCase() === 'auto' ? 'auto' : i18nMatch(h); if (v) { pref = v; try { localStorage.setItem(I18N_KEY, v); } catch (_) {} } }
  } catch (_) {}
  return pref;
})();
// langue effective : Auto = première langue de navigator.languages qui est disponible, sinon l'anglais
const LANG = (() => {
  if (LANG_PREF !== 'auto') return LANG_PREF;
  const list = (typeof navigator !== 'undefined' && ((navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language])) || [];
  for (const l of list) { const c = i18nMatch(l); if (c) return c; }
  return I18N.en ? 'en' : (I18N_LANGS[0] || 'en');
})();
const i18nHas = k => [LANG, 'en', 'fr'].some(l => I18N[l] && typeof I18N[l][k] === 'string');
function tr(key, ...a) {
  const v = [LANG, 'en', 'fr'].map(l => I18N[l] && I18N[l][key]).find(x => typeof x === 'string');
  const s = v === undefined ? key : v;
  return a.length ? s.replace(/\{(\d+)\}/g, (m, i) => (a[i] === undefined ? m : String(a[i]))) : s;
}
// pluriel : clé.one / clé.other (et .zero .two .few .many selon la langue) ; {0} = n
const i18nPR = (() => { try { return new Intl.PluralRules(LANG); } catch (_) { return null; } })();
function trn(key, n, ...a) {
  const cat = i18nPR ? i18nPR.select(n) : (n === 1 ? 'one' : 'other');
  return tr(i18nHas(key + '.' + cat) ? key + '.' + cat : key + '.other', n, ...a);
}
// langue des dates et des nombres (jj/mm/aaaa pour le français et l'anglais)
const i18nLocale = LANG === 'en' ? 'en-GB' : (LANG === 'fr' ? 'fr-FR' : LANG);
const i18nNum = (n, d) => Number(n).toLocaleString(LANG, { minimumFractionDigits: d, maximumFractionDigits: d });
// textes du document : data-i18n (contenu), data-i18n-title, data-i18n-ph (placeholder), data-i18n-aria (aria-label)
function applyI18n(root) {
  root = root || document;
  const sets = [['data-i18n', (e, v) => { e.textContent = v; }], ['data-i18n-title', (e, v) => e.setAttribute('title', v)], ['data-i18n-ph', (e, v) => e.setAttribute('placeholder', v)], ['data-i18n-aria', (e, v) => e.setAttribute('aria-label', v)]];
  for (const [attr, set] of sets) for (const e of root.querySelectorAll('[' + attr + ']')) set(e, tr(e.getAttribute(attr)));
  if (root === document) document.documentElement.lang = LANG;
}
// liste pour un sélecteur de langue : Auto puis chaque langue disponible, avec son propre nom
const i18nChoices = () => [['auto', tr('common.auto')]].concat(I18N_LANGS.map(c => [c, i18nName(c)]));
// change la langue : mémorise, retire #lang= de l'adresse (sinon il l'emporterait), recharge la page
function setLangPref(v) {
  try { localStorage.setItem(I18N_KEY, v === 'auto' || I18N[v] ? v : 'auto'); } catch (_) {}
  try { const u = new URL(location.href), hp = hashParams(u.hash); hp.delete('lang'); const hs = hp.toString(); history.replaceState(null, '', u.pathname + u.search + (hs ? '#' + hs : '')); } catch (_) {}
  location.reload();
}
