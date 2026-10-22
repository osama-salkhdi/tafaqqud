// Service Worker: يسمح بفتح الصفحة وإعادة تحميلها بدون إنترنت بعد أول فتح
const CACHE = "tafaqqud-v1";
self.addEventListener("install", e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./"])).catch(() => {}));
});
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

const timeout = ms => new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms));
const put = (req, res) => { if (res && (res.ok || res.type === "opaque")) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); } return res; };

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const u = new URL(req.url);
  if (u.origin === location.origin) {
    if (u.pathname.startsWith("/api/")) return;          // بيانات التفقد لا تُخزَّن هنا
    // الصفحة: من الشبكة أولاً، ومن الذاكرة عند الانقطاع أو عندما يكون السيرفر نائماً
    e.respondWith(
      Promise.race([fetch(req), timeout(5000)]).then(res => put(req, res))
        .catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match("./")))
    );
  } else if (["fonts.googleapis.com", "fonts.gstatic.com"].includes(u.hostname)) {
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => put(req, res))));
  }
});
