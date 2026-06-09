import { Eye, FileText, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listBatches, PACKAGE_TYPES } from "../api/barcodesApi";
import { getSelectedDepartment } from "../api/departmentsApi";
import { getErrorMessage } from "../api/http";
import type { GeneratedBatchItem } from "../api/types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { Select } from "../components/Select";
import { Table } from "../components/Table";
import { Header } from "../layout/Header";
import { formatDate, nullable } from "../utils/format";

const PAGE_LIMIT = 20;

export function HistoryPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<GeneratedBatchItem[]>([]);
  const [offset, setOffset] = useState(0);
  const [packageType, setPackageType] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadBatches(): Promise<void> {
    setLoading(true);
    setError(null);

    const parsedDepartmentId = Number(departmentId);

    try {
      setItems(
        await listBatches({
          limit: PAGE_LIMIT,
          offset,
          package_type: packageType || undefined,
          department_id:
            departmentId.trim() && Number.isInteger(parsedDepartmentId)
              ? parsedDepartmentId
              : undefined,
        }),
      );
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadBatches();
  }, [offset, packageType]);

  function applySelectedDepartment(): void {
    const selectedDepartment = getSelectedDepartment();

    if (selectedDepartment) {
      setDepartmentId(String(selectedDepartment.id));
      setOffset(0);
    }
  }

  return (
    <section>
      <Header
        title="History"
        description="Список созданных партий с фильтрами и пагинацией."
        actions={
          <Button icon={<RefreshCw size={15} />} loading={loading} onClick={loadBatches}>
            Refresh
          </Button>
        }
      />

      <div className="panel">
        <div className="filters-row">
          <Select
            label="Package type"
            value={packageType}
            onChange={(event) => {
              setPackageType(event.target.value);
              setOffset(0);
            }}
          >
            <option value="">All</option>
            {PACKAGE_TYPES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </Select>

          <Input
            label="Department ID"
            placeholder="50"
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value.replace(/\D/g, ""))}
          />

          <div className="filter-actions">
            <Button type="button" onClick={applySelectedDepartment}>
              Use selected
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={() => {
                setOffset(0);
                void loadBatches();
              }}
            >
              Apply
            </Button>
          </div>
        </div>

        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? <div className="inline-loader">Loading batches...</div> : null}

        {!loading && items.length === 0 ? (
          <EmptyState title="Batches not found" description="Измените фильтры или создайте batch." />
        ) : null}

        {items.length > 0 ? (
          <Table>
            <thead>
              <tr>
                <th>Batch</th>
                <th>Type</th>
                <th>Department</th>
                <th>Quantity</th>
                <th>First</th>
                <th>Last</th>
                <th>Generated</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((batch) => (
                <tr
                  className="clickable-row"
                  key={batch.id}
                  onClick={() => navigate(`/app/history/${batch.id}`)}
                >
                  <td className="mono">#{batch.id}</td>
                  <td>
                    <Badge variant="brand">{batch.package_type}</Badge>
                  </td>
                  <td>{nullable(batch.department_id)}</td>
                  <td>{batch.quantity}</td>
                  <td className="mono">{batch.first_barcode}</td>
                  <td className="mono">{batch.last_barcode}</td>
                  <td>{formatDate(batch.generated_at)}</td>
                  <td>
                    <div className="row-actions">
                      <button
                        aria-label="Open detail"
                        className="icon-button"
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          navigate(`/app/history/${batch.id}`);
                        }}
                      >
                        <Eye size={15} />
                      </button>
                      <button
                        aria-label="Open PDF"
                        className="icon-button"
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          navigate(`/app/pdf/${batch.id}`);
                        }}
                      >
                        <FileText size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : null}

        <div className="pagination">
          <span>
            Offset {offset}, limit {PAGE_LIMIT}
          </span>
          <div className="inline-actions">
            <Button
              disabled={offset === 0 || loading}
              onClick={() => setOffset((current) => Math.max(0, current - PAGE_LIMIT))}
            >
              Previous
            </Button>
            <Button
              disabled={items.length < PAGE_LIMIT || loading}
              onClick={() => setOffset((current) => current + PAGE_LIMIT)}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
