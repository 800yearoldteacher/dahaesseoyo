/* ---- 시험용 가짜 Firebase: 같은 브라우저의 여러 탭이 하나의 기록장을 나눠 씁니다 ---- */
const M = window.__MOCK || (window.__MOCK = (() => {
  const core = { docs: {}, listeners: new Set(), authListeners: new Set(), user: null };
  try { core.docs = JSON.parse(localStorage.getItem('mockdb') || '{}'); } catch (e) { core.docs = {}; }
  try { core.user = JSON.parse(sessionStorage.getItem('mockauth') || 'null'); } catch (e) { core.user = null; }
  const bc = new BroadcastChannel('mockdb');
  const parentOf = (p) => p.split('/').slice(0, -1).join('/');
  core.notify = (paths, local) => {
    for (const l of core.listeners) {
      if ((l.kind === 'doc' && paths.includes(l.path)) || (l.kind === 'col' && paths.some((p) => parentOf(p) === l.path))) setTimeout(() => l.emit(local), 0);
    }
  };
  const applyRaw = (changes) => { for (const c of changes) { if (c.data === null) delete core.docs[c.path]; else core.docs[c.path] = c.data; } };
  core.apply = (changes) => {
    applyRaw(changes);
    localStorage.setItem('mockdb', JSON.stringify(core.docs));
    bc.postMessage({ changes });
    core.notify(changes.map((c) => c.path), true);
  };
  bc.onmessage = (ev) => { applyRaw(ev.data.changes); core.notify(ev.data.changes.map((c) => c.path), false); };
  const TEACHER = () => window.__MOCK_TEACHER_EMAIL || 'teacher@test.com';
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const changedKeys = (a, b) => { const ks = new Set([...Object.keys(a || {}), ...Object.keys(b || {})]); return [...ks].filter((k) => !same((a || {})[k], (b || {})[k])); };
  const isTeacher = (u) => !!(u && !u.isAnonymous && u.emailVerified && u.email === TEACHER());
  const isApproved = (u) => !!(u && core.docs['devices/' + u.uid] && core.docs['devices/' + u.uid].approved === true);
  const canView = (u) => isTeacher(u) || isApproved(u);
  /* 보안 규칙 파일과 같은 판단을 자바스크립트로 옮긴 것 */
  core.allow = (op, path, before, after) => {
    const u = core.user;
    if (!u) return false;
    const seg = path.split('/');
    const [col, id] = seg;
    const read = op === 'get' || op === 'list';
    if (col === 'boards' && seg[2] === 'days' && window.__MOCK_DENY_DAYS) return false;   /* 예전 규칙 흉내 */
    if (col === 'boards' && seg[2] === 'days') {   /* 매일 반복 판의 날짜별 기록 */
      if (read) return canView(u);
      if (op === 'delete') return isTeacher(u);
      if (isTeacher(u)) return true;
      if (!isApproved(u)) return false;
      if (op === 'create') return Object.keys(after).every((k) => k === 'done') && after.done && Object.keys(after.done).length === 1;
      if (!changedKeys(before, after).every((k) => k === 'done')) return false;
      if (!after.done || !before.done) return false;
      return changedKeys(before.done, after.done).length === 1;
    }
    if (col === 'settings' || col === 'roster') return read ? canView(u) : isTeacher(u);
    if (col === 'boards') {
      if (read) return canView(u);
      if (op === 'create' || op === 'delete') return isTeacher(u);
      if (isTeacher(u)) return true;
      if (!isApproved(u)) return false;
      if (!changedKeys(before, after).every((k) => k === 'done')) return false;
      if (!after.done || !before.done) return false;
      return changedKeys(before.done, after.done).length === 1;
    }
    if (col === 'devices') {
      if (op === 'list') return isTeacher(u);
      if (op === 'get') return isTeacher(u) || u.uid === id;
      if (op === 'create') return u.uid === id && after.approved === false && Object.keys(after).every((k) => ['code', 'approved', 'createdAt', 'lastSeen', 'agent'].includes(k));
      if (op === 'update') return isTeacher(u) || (u.uid === id && changedKeys(before, after).every((k) => k === 'lastSeen'));
      if (op === 'delete') return isTeacher(u);
    }
    return false;
  };
  core.setUser = (u) => {
    core.user = u;
    sessionStorage.setItem('mockauth', JSON.stringify(u));
    core.authListeners.forEach((f) => setTimeout(() => f(u), 0));
  };
  core.writes = 0;
  return core;
})());
