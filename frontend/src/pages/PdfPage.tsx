import { Download, Eye, FileText, RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getBatchDetail, previewBatchPdf, printBatchPdf } from "../api/barcodesApi";
import { getErrorMessage } from "../api/http";
import type { GeneratedBatchDetail } from "../api/types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { PdfViewer } from "../components/PdfViewer";
import { Textarea } from "../components/Textarea";
import { Header } from "../layout/Header";
import { downloadBlob, formatDate, nullable } from "../utils/format";

export function PdfPage() {
  const navigate = useNavigate();
  const params = useParams();
  const routeBatchId = params.batchId ? Number(params.batchId) : null;
  const [batchIdInput, setBatchIdInput] = useState(
    params.batchId ?? localStorage.getItem("qazpost.lastBatchId") ?? "",
  );
  const [batch, setBatch] = useState<GeneratedBatchDetail | null>(null);
  const [pdfBlob, setPdfBlob] = useState<Blob | null>(null);
  const [notes, setNotes] = useState("");
  const [loadingBatch, setLoadingBatch] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [printing, setPrinting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const activeBatchId = routeBatchId && Number.isInteger(routeBatchId) ? routeBatchId : null;

  async function loadBatch(batchId: number): Promise<void> {
    setLoadingBatch(true);
    setError(null);

    try {
      setBatch(await getBatchDetail(batchId));
    } catch (requestError) {
      setBatch(null);
      setError(getErrorMessage(requestError));
    } finally {
      setLoadingBatch(false);
    }
  }

  async function loadPreview(batchId: number): Promise<void> {
    setLoadingPreview(true);
    setError(null);

    try {
      setPdfBlob(await previewBatchPdf(batchId));
    } catch (requestError) {
      setPdfBlob(null);
      setError(getErrorMessage(requestError));
    } finally {
      setLoadingPreview(false);
    }
  }

  useEffect(() => {
    if (activeBatchId) {
      localStorage.setItem("qazpost.lastBatchId", String(activeBatchId));
      setBatchIdInput(String(activeBatchId));
      void loadBatch(activeBatchId);
      void loadPreview(activeBatchId);
    }
  }, [activeBatchId]);

  function handleOpenBatch(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextBatchId = Number(batchIdInput);

    if (!Number.isInteger(nextBatchId) || nextBatchId <= 0) {
      setError("Введите корректный batch_id.");
      return;
    }

    navigate(`/app/pdf/${nextBatchId}`);
  }

  async function handlePrintAndDownload(): Promise<void> {
    if (!activeBatchId) {
      setError("Сначала откройте batch.");
      return;
    }

    setPrinting(true);
    setError(null);
    setSuccess(null);

    try {
      const blob = await printBatchPdf(activeBatchId, {
        printer_name: "Browser download",
        notes: notes.trim() || null,
      });
      downloadBlob(blob, `barcodes_batch_${activeBatchId}.pdf`);
      setSuccess("PDF скачан, batch обновлен как printed.");
      await loadBatch(activeBatchId);
      await loadPreview(activeBatchId);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setPrinting(false);
    }
  }

  return (
    <section>
      <Header
        title="PDF / Print"
        description="Предпросмотр PDF и отметка партии как printed."
        actions={
          activeBatchId ? (
            <Button
              icon={<RefreshCw size={15} />}
              loading={loadingBatch || loadingPreview}
              onClick={() => {
                void loadBatch(activeBatchId);
                void loadPreview(activeBatchId);
              }}
            >
              Refresh
            </Button>
          ) : null
        }
      />

      <div className="alert alert-warning">
        Backend не управляет физическим принтером напрямую. Браузер скачивает PDF, а печать
        запускается пользователем через системное окно печати.
      </div>

      <div className="pdf-grid">
        <div className="stack">
          <form className="panel batch-open-form" onSubmit={handleOpenBatch}>
            <Input
              label="Batch ID"
              min={1}
              placeholder="1"
              type="number"
              value={batchIdInput}
              onChange={(event) => setBatchIdInput(event.target.value)}
            />
            <Button icon={<FileText size={15} />} type="submit" variant="primary">
              Open
            </Button>
          </form>

          <div className="panel">
            <h2>Batch summary</h2>
            {loadingBatch ? <div className="inline-loader">Loading batch...</div> : null}
            {!batch && !loadingBatch ? (
              <EmptyState
                title="Batch is not opened"
                description="Откройте /app/pdf/:batchId или введите batch ID."
              />
            ) : null}
            {batch ? (
              <div className="stack compact">
                <div className="result-header">
                  <Badge variant="brand">{batch.package_type}</Badge>
                  <Badge variant="neutral">#{batch.id}</Badge>
                  <Badge variant="success">{batch.quantity} items</Badge>
                </div>
                <dl className="summary-list">
                  <div>
                    <dt>Department ID</dt>
                    <dd>{nullable(batch.department_id)}</dd>
                  </div>
                  <div>
                    <dt>Generated</dt>
                    <dd>{formatDate(batch.generated_at)}</dd>
                  </div>
                  <div>
                    <dt>First barcode</dt>
                    <dd className="mono">{batch.first_barcode}</dd>
                  </div>
                  <div>
                    <dt>Last barcode</dt>
                    <dd className="mono">{batch.last_barcode}</dd>
                  </div>
                  <div>
                    <dt>Printed count</dt>
                    <dd>
                      {batch.barcodes.filter((barcode) => barcode.printed).length} /{" "}
                      {batch.barcodes.length}
                    </dd>
                  </div>
                </dl>
              </div>
            ) : null}
          </div>

          <div className="panel">
            <Textarea
              label="Notes for print history"
              placeholder="printed from frontend"
              rows={3}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />

            <div className="inline-actions">
              <Button
                disabled={!activeBatchId}
                icon={<Eye size={15} />}
                loading={loadingPreview}
                onClick={() => {
                  if (activeBatchId) {
                    void loadPreview(activeBatchId);
                  }
                }}
              >
                Preview PDF
              </Button>
              <Button
                disabled={!activeBatchId}
                icon={<Download size={15} />}
                loading={printing}
                variant="primary"
                onClick={handlePrintAndDownload}
              >
                Скачать PDF и отметить как напечатано
              </Button>
            </div>

            {success ? <div className="alert alert-success">{success}</div> : null}
            {error ? <div className="alert alert-danger">{error}</div> : null}
          </div>
        </div>

        <PdfViewer blob={pdfBlob} />
      </div>
    </section>
  );
}
