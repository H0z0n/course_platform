export type VideoSource =
  | { kind: "embed"; src: string }
  | { kind: "file"; src: string }
  | { kind: "link"; src: string };

const YOUTUBE_PATH = /^\/(?:embed|shorts|live)\/([\w-]{6,})/;
const VK_VIDEO = /video(-?\d+)_(\d+)/;

function embed(src: string): VideoSource {
  return { kind: "embed", src };
}

function youtube(id: string): VideoSource {
  return embed(`https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}`);
}

function vk(url: URL): VideoSource | null {
  if (url.pathname === "/video_ext.php" && url.searchParams.get("oid") && url.searchParams.get("id")) {
    return embed(url.href);
  }
  const match = (url.pathname + (url.searchParams.get("z") ?? "")).match(VK_VIDEO);
  if (!match) return null;
  return embed(`https://vk.com/video_ext.php?oid=${match[1]}&id=${match[2]}&hd=2`);
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
    if (id) return embed(`https://player.vimeo.com/video/${id}`);
  }
  if (host === "player.vimeo.com") return embed(parsed.href);
  if (host === "kinescope.io") {
    const id = parsed.pathname.match(/^\/(?:embed\/)?([\w-]+)\/?$/)?.[1];
    if (id) return embed(`https://kinescope.io/embed/${id}`);
  }
  if (host === "vk.com" || host === "vkvideo.ru" || host === "vk.ru") {
    const source = vk(parsed);
    if (source) return source;
  }
  if (host === "rutube.ru") {
    const id = parsed.pathname.match(/^\/(?:video|play\/embed)\/([\da-f]{32})/)?.[1];
    if (id) return embed(`https://rutube.ru/play/embed/${id}`);
  }
  if (/\.(mp4|webm|ogg|ogv|mov|m4v)$/i.test(parsed.pathname)) return { kind: "file", src: parsed.href };
  return { kind: "link", src: parsed.href };
}
