import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listPrintHistory } from "../api/barcodesApi";
import { getSelectedDepartment } from "../api/departmentsApi";
import { getErrorMessage } from "../api/http";
import type { PrintedBatchItem } from "../api/types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { Table } from "../components/Table";
import { Header } from "../layout/Header";
import { formatDate, nullable } from "../utils/format";

const PAGE_LIMIT = 20;

export function PrintHistoryPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<PrintedBatchItem[]>([]);
  const [offset, setOffset] = useState(0);
  const [departmentId, setDepartmentId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadItems(): Promise<void> {
    setLoading(true);
    setError(null);

    const parsedDepartmentId = Number(departmentId);
    const parsedBatchId = Number(batchId);

    try {
      setItems(
        await listPrintHistory({
          limit: PAGE_LIMIT,
          offset,
          department_id:
            departmentId.trim() && Number.isInteger(parsedDepartmentId)
              ? parsedDepartmentId
              : undefined,
          generated_batch_id:
            batchId.trim() && Number.isInteger(parsedBatchId) ? parsedBatchId : undefined,
        }),
      );
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadItems();
  }, [offset]);

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
        title="Print History"
        description="Журнал скачивания PDF и отметок печати."
        actions={
          <Button icon={<RefreshCw size={15} />} loading={loading} onClick={loadItems}>
            Refresh
          </Button>
        }
      />

      <div className="panel">
        <div className="filters-row">
          <Input
            label="Batch ID"
            placeholder="1"
            value={batchId}
            onChange={(event) => setBatchId(event.target.value.replace(/\D/g, ""))}
          />
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
                void loadItems();
              }}
            >
              Apply
            </Button>
          </div>
        </div>

        {error ? <div className="alert alert-danger">{error}</div> : null}
        {loading ? <div className="inline-loader">Loading print history...</div> : null}

        {!loading && items.length === 0 ? (
          <EmptyState
            title="Print history is empty"
            description="После POST /pdf здесь появятся записи PrintedBatch."
          />
        ) : null}

        {items.length > 0 ? (
          <Table>
            <thead>
              <tr>
                <th>Batch ID</th>
                <th>Department ID</th>
                <th>Printed count</th>
                <th>First barcode</th>
                <th>Last barcode</th>
                <th>Printed by</th>
                <th>Printer</th>
                <th>Status</th>
                <th>Printed at</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  className="clickable-row"
                  key={item.id}
                  onClick={() => navigate(`/app/history/${item.generated_batch_id}`)}
                >
                  <td className="mono">#{item.generated_batch_id}</td>
                  <td>{nullable(item.department_id)}</td>
                  <td>{item.printed_count}</td>
                  <td className="mono">{item.first_barcode}</td>
                  <td className="mono">{item.last_barcode}</td>
                  <td>{nullable(item.printed_by)}</td>
                  <td>{nullable(item.printer_name)}</td>
                  <td>
                    <Badge variant="success">{item.status}</Badge>
                  </td>
                  <td>{formatDate(item.printed_at)}</td>
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
