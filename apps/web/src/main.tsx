import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const API_BASE = "https://683d9934b3e4c6.app.lhr.life";

const origFetch = window.fetch.bind(window);
window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
  if (typeof input === "string" && input.startsWith("/api")) {
    return origFetch(`${API_BASE}${input}`, init);
  }
  return origFetch(input, init);
};

const OrigEventSource = window.EventSource;
window.EventSource = class extends OrigEventSource {
  constructor(url: string | URL, eventSourceInitDict?: EventSourceInit) {
    const fixedUrl = typeof url === "string" && url.startsWith("/api") ? `${API_BASE}${url}` : url;
    super(fixedUrl, eventSourceInitDict);
  }
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)