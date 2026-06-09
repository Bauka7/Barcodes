import { Eye, FileText, FolderTree, RefreshCw, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { generateBarcodeNumbers, PACKAGE_TYPES } from "../api/barcodesApi";
import { getSelectedDepartment } from "../api/departmentsApi";
import { getErrorMessage } from "../api/http";
import type { BarcodeNumberResponse, SelectedDepartment } from "../api/types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { Select } from "../components/Select";
import { Table } from "../components/Table";
import { Textarea } from "../components/Textarea";
import { Header } from "../layout/Header";

export function GenerateBarcodePage() {
  const navigate = useNavigate();
  const [selectedDepartment, setSelectedDepartment] = useState<SelectedDepartment | null>(null);
  const [packageType, setPackageType] = useState("KG");
  const [quantity, setQuantity] = useState(1);
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<BarcodeNumberResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedDepartment(getSelectedDepartment());
  }, []);

  function refreshSelectedDepartment(): void {
    setSelectedDepartment(getSelectedDepartment());
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setResult(null);

    const normalizedPackageType = packageType.trim().toUpperCase();

    if (!selectedDepartment) {
      setError("Сначала выберите department_id на странице Departments.");
      return;
    }

    if (!PACKAGE_TYPES.includes(normalizedPackageType as (typeof PACKAGE_TYPES)[number])) {
      setError("Package type должен быть из списка backend seed.");
      return;
    }

    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) {
      setError("Quantity должен быть от 1 до 1000.");
      return;
    }

    setLoading(true);

    try {
      const response = await generateBarcodeNumbers({
        package_type: normalizedPackageType,
        quantity,
        department_id: selectedDepartment.id,
        notes: notes.trim() || null,
      });
      setResult(response);
      localStorage.setItem("qazpost.lastBatchId", String(response.batch_id));
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <Header
        title="Generate Barcode"
        description="Сформировать партию SHPI для выбранного отделения."
      />

      <div className="split-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="selected-strip">
            <div>
              <div className="muted-label">Selected department</div>
              {selectedDepartment ? (
                <div>
                  <strong>{selectedDepartment.name}</strong>
                  <div className="muted mono">
                    ID {selectedDepartment.id} · {selectedDepartment.code}
                  </div>
                </div>
              ) : (
                <span className="muted">Department is not selected.</span>
              )}
            </div>
            <div className="inline-actions">
              <Button
                icon={<RefreshCw size={15} />}
                type="button"
                onClick={refreshSelectedDepartment}
              >
                Refresh
              </Button>
              <Button
                icon={<FolderTree size={15} />}
                type="button"
                onClick={() => navigate("/app/departments")}
              >
                Select
              </Button>
            </div>
          </div>

          <div className="form-grid">
            <Select
              label="Package type"
              name="package_type"
              value={packageType}
              onChange={(event) => setPackageType(event.target.value.toUpperCase())}
            >
              {PACKAGE_TYPES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>

            <Input
              label="Quantity"
              max={1000}
              min={1}
              name="quantity"
              type="number"
              value={quantity}
              onChange={(event) => setQuantity(Number(event.target.value))}
            />
          </div>

          <Textarea
            label="Notes"
            name="notes"
            placeholder="Опционально"
            rows={4}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />

          {error ? <div className="alert alert-danger">{error}</div> : null}

          <Button
            icon={<Sparkles size={15} />}
            loading={loading}
            type="submit"
            variant="primary"
          >
            Сгенерировать
          </Button>
        </form>

        <aside className="panel">
          <h2>Result</h2>
          {!result ? (
            <EmptyState
              title="Batch не создан"
              description="После генерации здесь появятся batch_id, диапазон и список SHPI."
            />
          ) : (
            <div className="result-stack">
              <div className="result-header">
                <Badge variant="success">Batch #{result.batch_id}</Badge>
                <Badge variant="brand">{result.count} items</Badge>
              </div>

              <dl className="summary-list">
                <div>
                  <dt>First barcode</dt>
                  <dd className="mono">{result.first_barcode}</dd>
                </div>
                <div>
                  <dt>Last barcode</dt>
                  <dd className="mono">{result.last_barcode}</dd>
                </div>
              </dl>

              <div className="inline-actions">
                <Button
                  icon={<Eye size={15} />}
                  type="button"
                  onClick={() => navigate(`/app/history/${result.batch_id}`)}
                >
                  Open detail
                </Button>
                <Button
                  icon={<FileText size={15} />}
                  type="button"
                  variant="primary"
                  onClick={() => navigate(`/app/pdf/${result.batch_id}`)}
                >
                  Preview PDF
                </Button>
              </div>

              <Table className="items-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>SHPI</th>
                  </tr>
                </thead>
                <tbody>
                  {result.items.map((barcode, index) => (
                    <tr key={barcode}>
                      <td>{index + 1}</td>
                      <td className="mono">{barcode}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </aside>
      </div>

      {!selectedDepartment ? (
        <div className="under-note">
          <Link to="/app/departments">Departments</Link> нужно выбрать перед генерацией, чтобы
          отправить настоящий `department_id`.
        </div>
      ) : null}
    </section>
  );
}
