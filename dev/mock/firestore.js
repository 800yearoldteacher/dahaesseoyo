class DocRef { constructor(path) { this.path = path; this.id = path.split('/').pop(); } }
class ColRef { constructor(path) { this.path = path; this.id = path; } }
class QueryRef { constructor(col, cons) { this.col = col; this.path = col.path; this.cons = cons; } }
export const documentId = () => ({ __docId: true });
export const where = (f, op, v) => ({ f, op, v });
export const query = (col, ...cons) => new QueryRef(col, cons);
const pass = (id, cons) => cons.every((c) => { const a = id, b = c.v; return c.op === '>=' ? a >= b : c.op === '<=' ? a <= b : c.op === '>' ? a > b : c.op === '<' ? a < b : c.op === '==' ? a === b : true; });
export class FieldPath { constructor(...segs) { this.segs = segs; } }
const DEL = { __op: 'del' };
export const deleteField = () => DEL;
export const increment = (n) => ({ __op: 'inc', n });
export const initializeFirestore = () => ({});
export const getFirestore = () => ({});
export const persistentLocalCache = () => ({});
export const persistentMultipleTabManager = () => ({});
export function doc(a, ...segs) {
  if (a instanceof ColRef) return new DocRef(a.path + '/' + (segs.length ? segs.join('/') : 'auto' + Math.random().toString(36).slice(2, 12)));
  return new DocRef(segs.join('/'));
}
export function collection(db, ...segs) { return new ColRef(segs.join('/')); }
const copy = (x) => (x === undefined ? undefined : JSON.parse(JSON.stringify(x)));
const perm = () => { const e = new Error('Missing or insufficient permissions.'); e.code = 'permission-denied'; return e; };
function snapDoc(path, local, docs) {
  const data = (docs || M.docs)[path];
  return { id: path.split('/').pop(), ref: new DocRef(path), exists: () => data !== undefined, data: () => copy(data), metadata: { hasPendingWrites: !!local, fromCache: false } };
}
export function getDoc(ref) {
  return new Promise((res, rej) => setTimeout(() => (M.allow('get', ref.path, M.docs[ref.path] || {}, {}) ? res(snapDoc(ref.path, false)) : rej(perm())), 5));
}
function parseArgs(args) {
  const out = [];
  if (args.length === 1 && !(args[0] instanceof FieldPath)) { for (const [k, v] of Object.entries(args[0])) out.push([k.split('.'), v]); }
  else for (let i = 0; i < args.length; i += 2) out.push([args[i] instanceof FieldPath ? args[i].segs : String(args[i]).split('.'), args[i + 1]]);
  return out;
}
function applyFields(base, fields) {
  const o = copy(base);
  for (const [segs, v] of fields) {
    let t = o;
    for (let i = 0; i < segs.length - 1; i++) { if (typeof t[segs[i]] !== 'object' || t[segs[i]] === null) t[segs[i]] = {}; t = t[segs[i]]; }
    const k = segs[segs.length - 1];
    if (v === DEL) delete t[k]; else if (v && v.__op === 'inc') t[k] = (Number(t[k]) || 0) + v.n; else t[k] = copy(v);
  }
  return o;
}
function deepMerge(base, add) {
  const o = copy(base || {});
  for (const [k, v] of Object.entries(add)) {
    if (v === DEL) delete o[k];
    else if (v && typeof v === 'object' && !Array.isArray(v) && !v.__op && o[k] && typeof o[k] === 'object' && !Array.isArray(o[k])) o[k] = deepMerge(o[k], v);
    else if (v && v.__op === 'inc') o[k] = (Number(o[k]) || 0) + v.n;
    else o[k] = copy(v);
  }
  return o;
}
function op(docs, kind, ref, payload, opts) {
  const before = docs[ref.path];
  if (kind === 'set') {
    const after = opts && opts.merge ? deepMerge(before, payload) : copy(payload);
    if (!M.allow(before === undefined ? 'create' : 'update', ref.path, before || {}, after)) throw perm();
    return { path: ref.path, data: after };
  }
  if (kind === 'update') {
    if (before === undefined) { const e = new Error('No document to update'); e.code = 'not-found'; throw e; }
    const after = applyFields(before, payload);
    if (!M.allow('update', ref.path, before, after)) throw perm();
    return { path: ref.path, data: after };
  }
  if (!M.allow('delete', ref.path, before || {}, {})) throw perm();
  return { path: ref.path, data: null };
}
function run(fn) {
  try { const ch = fn(); M.writes += ch.length; M.apply(ch); return new Promise((r) => setTimeout(r, 5)); }
  catch (e) { return Promise.reject(e); }
}
export const setDoc = (ref, data, opts) => run(() => [op(M.docs, 'set', ref, data, opts)]);
export const updateDoc = (ref, ...args) => run(() => [op(M.docs, 'update', ref, parseArgs(args))]);
export const deleteDoc = (ref) => run(() => [op(M.docs, 'delete', ref)]);
export function writeBatch() {
  const ops = [];
  return {
    set(ref, d, o) { ops.push(['set', ref, d, o]); return this; },
    update(ref, ...a) { ops.push(['update', ref, parseArgs(a)]); return this; },
    delete(ref) { ops.push(['delete', ref]); return this; },
    commit() {
      return run(() => {
        const scratch = Object.assign({}, M.docs), out = [];
        for (const [k, ref, p, o] of ops) { const c = op(scratch, k, ref, p, o); if (c.data === null) delete scratch[c.path]; else scratch[c.path] = c.data; out.push(c); }
        return out;
      });
    }
  };
}
function listDocs(ref) {
  const pre = ref.path + '/';
  const cons = ref instanceof QueryRef ? ref.cons : [];
  return Object.keys(M.docs).filter((p) => p.startsWith(pre) && !p.slice(pre.length).includes('/') && pass(p.slice(pre.length), cons)).sort();
}
export function getDocs(ref) {
  return new Promise((res, rej) => setTimeout(() => {
    if (!M.allow('list', ref.path, {}, {})) { rej(perm()); return; }
    const docs = listDocs(ref).map((p) => snapDoc(p, false));
    res({ docs, size: docs.length, empty: !docs.length, forEach: (f) => docs.forEach(f) });
  }, 5));
}
export function onSnapshot(ref, next, error) {
  const isCol = ref instanceof ColRef || ref instanceof QueryRef;
  const l = { kind: isCol ? 'col' : 'doc', path: ref.path, prev: null, active: true };
  l.emit = (local) => {
    if (!l.active) return;
    if (!isCol) { next(snapDoc(ref.path, local)); return; }
    const paths = listDocs(ref);
    const now = {}; paths.forEach((p) => { now[p] = JSON.stringify(M.docs[p]); });
    const docs = paths.map((p) => snapDoc(p, local));
    const prev = l.prev || {}, changes = [];
    paths.forEach((p, i) => { if (!(p in prev)) changes.push({ type: 'added', doc: docs[i] }); else if (prev[p] !== now[p]) changes.push({ type: 'modified', doc: docs[i] }); });
    Object.keys(prev).forEach((p) => { if (!(p in now)) changes.push({ type: 'removed', doc: snapDoc(p, local, {}) }); });
    l.prev = now;
    next({ docs, size: docs.length, empty: !docs.length, forEach: (f) => docs.forEach(f), docChanges: () => changes, metadata: { hasPendingWrites: !!local, fromCache: false } });
  };
  setTimeout(() => {
    if (!M.allow(isCol ? 'list' : 'get', ref.path, M.docs[ref.path] || {}, {})) { l.active = false; if (error) error(perm()); return; }
    M.listeners.add(l);
    l.emit(false);
  }, 5);
  return () => { l.active = false; M.listeners.delete(l); };
}
