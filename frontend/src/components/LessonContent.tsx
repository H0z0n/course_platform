import { lazy, Suspense } from "react";
import type { ContentType } from "../api/types";
import { parseVideo } from "../lib/video";
import { Spinner } from "./ui";

const Markdown = lazy(() => import("./Markdown"));

export function MarkdownView({ source }: { source: string }) {
  return (
    <div className="prose">
      <Suspense fallback={<Spinner />}>
        <Markdown source={source} />
      </Suspense>
    </div>
  );
}

export function VideoPlayer({ url, title }: { url: string; title: string }) {
  const source = parseVideo(url);
  if (source === null) return <p className="muted">Видео пока не добавлено.</p>;

  if (source.kind === "embed") {
    return (
      <div className="video">
        <iframe
          src={source.src}
          title={title}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
          allowFullScreen
          referrerPolicy="strict-origin-when-cross-origin"
        />
      </div>
    );
  }
  if (source.kind === "file") {
    return (
      <div className="video">
        <video src={source.src} controls preload="metadata" />
      </div>
    );
  }
  return (
    <a className="btn" href={source.src} target="_blank" rel="noreferrer noopener">
      Открыть видео в новой вкладке
    </a>
  );
}

export function LessonContent({
  contentType,
  content,
  title,
}: {
  contentType: ContentType;
  content: string;
  title: string;
}) {
  if (contentType === "video") return <VideoPlayer url={content} title={title} />;
  if (!content.trim()) return <p className="muted">Текст урока пока не добавлен.</p>;
  return <MarkdownView source={content} />;
}
