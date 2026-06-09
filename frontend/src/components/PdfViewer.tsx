import { useEffect, useState } from "react";

import { EmptyState } from "./EmptyState";

interface PdfViewerProps {
  blob: Blob | null;
}

export function PdfViewer({ blob }: PdfViewerProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!blob) {
      setObjectUrl(null);
      return;
    }

    const url = URL.createObjectURL(blob);
    setObjectUrl(url);

    return () => URL.revokeObjectURL(url);
  }, [blob]);

  if (!objectUrl) {
    return (
      <div className="pdf-viewer empty-pdf">
        <EmptyState
          title="PDF preview is empty"
          description="Нажмите Preview PDF, чтобы получить файл от backend."
        />
      </div>
    );
  }

  return (
    <div className="pdf-viewer">
      <iframe src={objectUrl} title="PDF preview" />
    </div>
  );
}
