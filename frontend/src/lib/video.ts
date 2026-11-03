export type VideoSource =
  | { kind: "embed"; src: string }
  | { kind: "file"; src: string }
  | { kind: "link"; src: string };

const YOUTUBE_PATH = /^\/(?:embed|shorts|live)\/([\w-]{6,})/;

function youtube(id: string): VideoSource {
  return { kind: "embed", src: `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}` };
}

export function parseVideo(url: string): VideoSource | null {
  let parsed: URL;
  try {
    parsed = new URL(url.trim());
  } catch {
    return null;
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return null;

  const host = parsed.hostname.replace(/^(www|m)\./, "");
  if (host === "youtu.be") {
    const id = parsed.pathname.slice(1);
    if (/^[\w-]{6,}$/.test(id)) return youtube(id);
  }
  if (host === "youtube.com" || host === "youtube-nocookie.com") {
    const id = parsed.searchParams.get("v") ?? parsed.pathname.match(YOUTUBE_PATH)?.[1];
    if (id && /^[\w-]{6,}$/.test(id)) return youtube(id);
  }
  if (host === "vimeo.com") {
    const id = parsed.pathname.match(/^\/(\d+)/)?.[1];
    if (id) return { kind: "embed", src: `https://player.vimeo.com/video/${id}` };
  }
  if (host === "player.vimeo.com") return { kind: "embed", src: parsed.href };
  if (/\.(mp4|webm|ogg|ogv|mov|m4v)$/i.test(parsed.pathname)) return { kind: "file", src: parsed.href };
  return { kind: "link", src: parsed.href };
}
