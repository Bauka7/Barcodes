import { Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { searchBarcode } from "../api/barcodesApi";
import { getErrorMessage } from "../api/http";
import type { GeneratedBarcodeSearchResponse } from "../api/types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { Header } from "../layout/Header";
import { formatDate, nullable } from "../utils/format";

export function SearchPage() {
  const navigate = useNavigate();
  const [barcode, setBarcode] = useState("");
  const [result, setResult] = useState<GeneratedBarcodeSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setResult(null);
    setSearched(true);

    const normalizedBarcode = barcode.trim().toUpperCase();

    if (!normalizedBarcode) {
      setError("Введите SHPI для поиска.");
      return;
    }

    setBarcode(normalizedBarcode);
    setLoading(true);

    try {
      setResult(await searchBarcode(normalizedBarcode));
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <Header
        title="Search SHPI"
        description="Поиск SHPI в истории генерации."
      />

      <div className="panel">
        <form className="search-form" onSubmit={handleSubmit}>
          <Input
            label="Barcode"
            placeholder="KG015779068KZ"
            value={barcode}
            onChange={(event) => setBarcode(event.target.value)}
          />
          <Button icon={<Search size={15} />} loading={loading} type="submit" variant="primary">
            Найти
          </Button>
        </form>

        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? <div className="inline-loader">Searching...</div> : null}

        {!loading && searched && !result && !error ? (
          <EmptyState title="SHPI not found" description="Проверьте код и попробуйте снова." />
        ) : null}

        {result ? (
          <div className="search-result">
            <div className="result-header">
              <span className="mono result-code">{result.barcode}</span>
              <Badge variant={result.printed ? "success" : "neutral"}>
                {result.printed ? "Printed" : "Not printed"}
              </Badge>
            </div>

            <dl className="summary-grid">
              <div>
                <dt>Batch</dt>
                <dd>
                  <button
                    className="link-button mono"
                    type="button"
                    onClick={() => navigate(`/app/history/${result.batch_id}`)}
                  >
                    #{result.batch_id}
                  </button>
                </dd>
              </div>
              <div>
                <dt>Package type</dt>
                <dd>{result.package_type}</dd>
              </div>
              <div>
                <dt>Department ID</dt>
                <dd>{nullable(result.department_id)}</dd>
              </div>
              <div>
                <dt>Sequence</dt>
                <dd className="mono">{result.sequence_number}</dd>
              </div>
              <div>
                <dt>Generated at</dt>
                <dd>{formatDate(result.generated_at)}</dd>
              </div>
              <div>
                <dt>Printed at</dt>
                <dd>{formatDate(result.printed_at)}</dd>
              </div>
              <div>
                <dt>Batch first</dt>
                <dd className="mono">{result.batch.first_barcode}</dd>
              </div>
              <div>
                <dt>Batch last</dt>
                <dd className="mono">{result.batch.last_barcode}</dd>
              </div>
            </dl>
          </div>
        ) : null}
      </div>
    </section>
  );
}
