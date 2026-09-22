export function getAuth() { return { get currentUser() { return M.user; } }; }
export function onAuthStateChanged(auth, cb) { M.authListeners.add(cb); setTimeout(() => cb(M.user), 0); return () => M.authListeners.delete(cb); }
const fail = (code) => { const e = new Error(code); e.code = code; return e; };
export async function signInAnonymously() {
  if (window.__MOCK_ANON_ERROR) throw fail(window.__MOCK_ANON_ERROR);
  const u = { uid: 'anon' + Math.random().toString(36).slice(2, 10), isAnonymous: true, email: null, emailVerified: false };
  M.setUser(u); return { user: u };
}
export class GoogleAuthProvider {}
export async function signInWithPopup() {
  if (window.__MOCK_POPUP_ERROR) throw fail(window.__MOCK_POPUP_ERROR);
  const email = window.__MOCK_POPUP_EMAIL || 'teacher@test.com';
  const u = { uid: 'g' + email.replace(/\W/g, ''), isAnonymous: false, email, emailVerified: true };
  M.setUser(u); return { user: u };
}
export async function signOut() { M.setUser(null); }
