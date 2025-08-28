// Cloudflare Pages Functions middleware
// This file ensures proper routing for the SPA

export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  
  // If it's not an API call and not a static file, serve index.html
  if (!url.pathname.startsWith('/api/') && 
      !url.pathname.includes('.') && 
      url.pathname !== '/') {
    
    // Rewrite to index.html for SPA routing
    const newUrl = new URL('/index.html', request.url);
    return fetch(newUrl.toString(), {
      headers: request.headers
    });
  }
  
  return next();
}