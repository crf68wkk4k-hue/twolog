/* ============================================================================
   v25 테스트용 supabase-js 대역(stub)
   ----------------------------------------------------------------------------
   진짜 프로젝트(qvhupdivtfzhzymovtyy)에 시험용 계정·행을 만들지 않으려고,
   Playwright 가 esm.sh 모듈 요청을 이 파일로 바꿔 끼웁니다.
   sync.js 가 실제로 쓰는 부분(auth / from().select·insert·update·upsert·delete /
   rpc / storage / channel)만 흉내 냅니다. 앱 코드는 진짜 그대로 돌아갑니다.

   window.__STUB_SCHEMA_MISSING = true 로 열면
   "아직 SQL 스키마를 넣지 않은 프로젝트"처럼 모든 표가 없는 상황을 만듭니다.
   ========================================================================= */

const SESSION_KEY = "stub-sb-session";
/* 테스트 중 새로 열기(reload)에도 같은 서버 상태가 유지되도록 localStorage 에 둡니다 */
const DB_KEY = "stub-sb-db";

function db() {
  if (!window.__stub) {
    let restored = null;
    try { const raw = localStorage.getItem(DB_KEY); if (raw) restored = JSON.parse(raw); } catch (e) { restored = null; }
    window.__stub = restored || { users: {}, couples: [], events: [], notes: [], photos: [], settings: [], uploads: [], seq: 0 };
    ["couples", "events", "notes", "photos", "settings", "uploads"].forEach((k) => {
      if (!Array.isArray(window.__stub[k])) window.__stub[k] = [];
    });
    if (!window.__stub.users) window.__stub.users = {};
  }
  return window.__stub;
}

function persist() {
  try { localStorage.setItem(DB_KEY, JSON.stringify(db())); } catch (e) {}
}

function readSession() {
  try { const raw = localStorage.getItem(SESSION_KEY); return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
}
function writeSession(s) {
  try { if (s) localStorage.setItem(SESSION_KEY, JSON.stringify(s)); else localStorage.removeItem(SESSION_KEY); } catch (e) {}
}
function err(message) { return { data: null, error: { message: message } }; }
function uid(prefix) { return prefix + String(++db().seq) + Math.random().toString(36).slice(2, 6); }

class Query {
  constructor(table) {
    this.table = table;
    this.kind = "select";
    this.filters = [];
    this.payload = null;
    this.one = false;
  }
  select() { return this; }
  order() { return this; }
  limit() { return this; }
  eq(k, v) { this.filters.push([k, v, "eq"]); return this; }
  contains(k, v) { this.filters.push([k, v, "contains"]); return this; }
  insert(p) { this.kind = "insert"; this.payload = p; return this; }
  update(p) { this.kind = "update"; this.payload = p; return this; }
  upsert(p, opts) {
    this.kind = "upsert";
    this.payload = p;
    this.conflictKeys = opts && opts.onConflict ? String(opts.onConflict).split(",").map((s) => s.trim()) : null;
    return this;
  }
  delete() { this.kind = "delete"; return this; }
  single() { this.one = true; return this; }

  table_rows() { const t = db()[this.table]; return Array.isArray(t) ? t : []; }

  match(row) {
    return this.filters.every((f) => {
      const k = f[0], v = f[1], kind = f[2];
      if (kind === "contains") {
        const have = row[k];
        return Array.isArray(have) && Array.isArray(v) && v.every((x) => have.indexOf(x) >= 0);
      }
      return row[k] === v;
    });
  }

  run() {
    if (window.__STUB_SCHEMA_MISSING) {
      return err("Could not find the table 'public." + this.table + "' in the schema cache");
    }
    const rows = this.table_rows();
    if (this.kind === "select") {
      const hit = rows.filter((r) => this.match(r));
      if (this.one) return hit.length ? { data: hit[0], error: null } : err("no rows");
      return { data: hit, error: null };
    }
    if (this.kind === "insert") {
      const row = Object.assign({}, this.payload);
      if (!row.id) row.id = uid("row");
      rows.push(row);
      persist();
      if (this.one) return { data: row, error: null };
      return { data: [row], error: null };
    }
    if (this.kind === "upsert") {
      const list = Array.isArray(this.payload) ? this.payload : [this.payload];
      list.forEach((p) => {
        const row = Object.assign({}, p);
        const at = row.id
          ? rows.findIndex((r) => r.id === row.id)
          : rows.findIndex((r) => this.conflictKeys && this.conflictKeys.every((k) => r[k] === row[k]));
        if (at >= 0) Object.assign(rows[at], row);
        else rows.push(row);
      });
      persist();
      return { data: null, error: null };
    }
    if (this.kind === "update") {
      const hit = rows.filter((r) => this.match(r));
      hit.forEach((r) => Object.assign(r, this.payload));
      persist();
      return { data: hit, error: null };
    }
    if (this.kind === "delete") {
      const rest = rows.filter((r) => !this.match(r));
      db()[this.table] = rest;
      persist();
      return { data: null, error: null };
    }
    return err("unsupported");
  }

  then(onOk, onBad) {
    /* v36 테스트: window.__STUB_WRITE_DELAY(ms) 를 정해 두면 «쓰기» 응답만 그만큼 늦어집니다.
       (저장이 끝나기 전에 Realtime 이벤트가 오는 상황을 만들어 보려고 — 읽기는 그대로 빨라요) */
    const d = Number((typeof window !== "undefined" && window.__STUB_WRITE_DELAY) || 0);
    if (d > 0 && this.kind !== "select") {
      return new Promise((res) => setTimeout(res, d)).then(() => this.run()).then(onOk, onBad);
    }
    return Promise.resolve(this.run()).then(onOk, onBad);
  }
  catch(onBad) { return this.then(null, onBad); }
}

const TINY_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";

export function createClient(url, key, opts) {
  const auth = {
    getSession() {
      const s = readSession();
      return Promise.resolve({ data: { session: s }, error: null });
    },
    signInWithPassword(creds) {
      const email = String(creds.email || "").trim().toLowerCase();
      const user = Object.keys(db().users).map((k) => db().users[k]).find((u) => u.email === email);
      if (!user || user.password !== creds.password) {
        return Promise.resolve({ data: { session: null, user: null }, error: { message: "Invalid login credentials" } });
      }
      const session = { access_token: "stub-token", refresh_token: "stub-refresh", user: { id: user.id, email: user.email } };
      writeSession(session);
      return Promise.resolve({ data: { session: session, user: session.user }, error: null });
    },
    signUp(creds) {
      const email = String(creds.email || "").trim().toLowerCase();
      const users = db().users;
      let user = Object.keys(users).map((k) => users[k]).find((u) => u.email === email);
      if (!user) { user = { id: uid("user"), email: email, password: creds.password }; users[user.id] = user; }
      persist();
      const session = { access_token: "stub-token", refresh_token: "stub-refresh", user: { id: user.id, email: user.email } };
      writeSession(session);
      return Promise.resolve({ data: { session: session, user: session.user }, error: null });
    },
    signOut() { writeSession(null); return Promise.resolve({ error: null }); },
    onAuthStateChange() { return { data: { subscription: { unsubscribe() {} } } }; }
  };

  function from(table) { return new Query(table); }

  function rpc(name, args) {
    if (name === "join_couple_by_code") {
      const code = String((args && args.code) || "").replace(/\D/g, "");
      const session = readSession();
      const me = session && session.user ? session.user.id : null;
      if (!me) return Promise.resolve(err("not_authenticated"));
      const row = db().couples.find((c) => String(c.invite_code) === code);
      if (!row) return Promise.resolve(err("code_not_found"));
      if (row.members.indexOf(me) >= 0) return Promise.resolve({ data: row, error: null });
      if (row.members.length >= 2) return Promise.resolve(err("couple_full"));
      row.members = row.members.concat([me]);
      persist();
      return Promise.resolve({ data: row, error: null });
    }
    if (name === "leave_couple") {
      const session = readSession();
      const me = session && session.user ? session.user.id : null;
      db().couples.forEach((c) => { c.members = (c.members || []).filter((m) => m !== me); });
      persist();
      return Promise.resolve({ data: null, error: null });
    }
    return Promise.resolve(err("unknown_function"));
  }

  function storageFrom() {
    return {
      upload(path, blob) {
        const st = db();
        st.uploads = st.uploads || [];
        st.uploads.push({ path: path, size: (blob && blob.size) || 0, type: (blob && blob.type) || "" });
        persist();
        return Promise.resolve({ data: { path: path }, error: null });
      },
      createSignedUrl(path) { return Promise.resolve({ data: { signedUrl: TINY_GIF }, error: null }); },
      createSignedUrls(paths) {
        return Promise.resolve({ data: (paths || []).map((p) => ({ path: p, signedUrl: TINY_GIF })), error: null });
      },
      remove() { return Promise.resolve({ data: null, error: null }); }
    };
  }

  function channel() {
    const ch = {
      on(type, filter, cb) {
        if (typeof cb === "function") {
          window.__stubHandlers = window.__stubHandlers || [];
          window.__stubHandlers.push({ type: type, filter: filter || {}, cb: cb });
        }
        return ch;
      },
      subscribe(cb) { if (typeof cb === "function") setTimeout(() => cb("SUBSCRIBED"), 0); return ch; },
      unsubscribe() { return Promise.resolve("ok"); }
    };
    return ch;
  }

  return { auth: auth, from: from, rpc: rpc, storage: { from: storageFrom }, channel: channel, removeChannel() {} };
}

export default { createClient };

/* ----------------------------------------------------------------------------
   테스트에서 진짜 Realtime 이벤트를 흉내 낼 때:
     window.__stubEmit("settings", "<couple_id>")
   구독해 둔 postgres_changes 핸들러를 그대로 불러 줍니다(앱의 재구독·재읽기 경로 확인용).
   -------------------------------------------------------------------------- */
if (typeof window !== "undefined") {
  window.__stubEmit = function (table, filterValue) {
    const list = window.__stubHandlers || [];
    let hit = 0;
    list.forEach((h) => {
      const f = h.filter || {};
      if (f.table && f.table !== table) return;
      if (f.filter && filterValue && String(f.filter).indexOf(String(filterValue)) < 0) return;
      hit += 1;
      try { h.cb({ eventType: "*", table: table, new: {}, old: {} }); } catch (e) {}
    });
    return hit;
  };
}
