/* ============================================================================
   투로그 TwoLog — sw.js
   앱 껍데기(HTML·CSS·JS·아이콘·폰트)를 기기에 캐시해서
   홈 화면에서 열 때 바로 뜨고, 비행기 모드에서도 열리게 합니다.
   기록 자체는 sync.js 가 localStorage / IndexedDB / Supabase 에 보관합니다.
   ========================================================================= */
const VERSION = "twolog-v21";
const SHELL = "shell-" + VERSION;

const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./sync.js",
  "./app.js",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon.svg",
  "./icons/favicon-32.png",
  "./assets/fonts/nixgon-m.woff",   /* v21: 캘린더 글씨 — 닉스곤체 */
  "./assets/fonts/nixgon-b.woff",
  "./assets/fonts/pretendard-400.woff2",
  "./assets/fonts/pretendard-500.woff2",
  "./assets/fonts/pretendard-600.woff2",
  "./assets/fonts/pretendard-700.woff2"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL).then((cache) =>
      // 한 파일이 실패해도 설치는 계속되도록 개별 add
      // cache:"reload" — GitHub Pages 의 10분 HTTP 캐시를 건너뛰고 항상 새 파일을 담습니다
      Promise.all(ASSETS.map((url) => cache.add(new Request(url, { cache: "reload" })).catch(() => null)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  // v17: skipWaiting 으로 바로 활성화되고, 옛 버전 캐시는 여기서 지웁니다.
  //      (앱 화면은 app.js 의 controllerchange 리스너가 한 번만 새로고침해요)
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data === "skip-waiting") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  // 다른 출처(Supabase API, 폰트 CDN 모듈)는 서비스워커가 건드리지 않습니다.
  if (url.origin !== self.location.origin) return;

  // 화면 이동: 네트워크 우선, 실패하면 캐시된 index.html
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(SHELL).then((c) => c.put("./index.html", copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match("./index.html").then((hit) => hit || caches.match("./")))
    );
    return;
  }

  // 정적 파일: 캐시 우선 + 뒤에서 갱신(stale-while-revalidate)
  event.respondWith(
    caches.match(req).then((hit) => {
      const network = fetch(req)
        .then((res) => {
          if (res && res.status === 200 && res.type === "basic") {
            const copy = res.clone();
            caches.open(SHELL).then((c) => c.put(req, copy)).catch(() => {});
          }
          return res;
        })
        .catch(() => hit);
      return hit || network;
    })
  );
});
