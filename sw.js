// Dobry Talerz v2.8: zawsze pobieraj aktualny HTML, zachowaj działanie offline.
const CACHE='dobry-talerz-online-v2-8';
const CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(Promise.all([
    caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('dobry-talerz-online-v')&&key!==CACHE).map(key=>caches.delete(key)))),
    self.clients.claim()
  ]));
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;
  event.respondWith((async()=>{
    try{
      // GitHub Pages: używaj świeżej odpowiedzi zamiast starego HTML z pamięci.
      const liveRequest=request.mode==='navigate'?new Request(request,{cache:'no-store'}):request;
      const response=await fetch(liveRequest);
      if(response.ok){
        const cache=await caches.open(CACHE);
        // Wszystkie warianty adresu z parametrem ?dt_refresh zapisuj jako ten sam dokument offline.
        const key=request.mode==='navigate'?new URL('./index.html',self.registration.scope).href:request;
        event.waitUntil(cache.put(key,response.clone()));
      }
      return response;
    }catch(err){
      const cache=await caches.open(CACHE);
      return (await cache.match(request))||(request.mode==='navigate'?await cache.match('./index.html'):undefined)||Response.error();
    }
  })());
});
