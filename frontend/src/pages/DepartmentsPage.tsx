import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  getDepartmentsTree,
  getSelectedDepartment,
  saveSelectedDepartment,
} from "../api/departmentsApi";
import type { DepartmentTreeItem, SelectedDepartment } from "../api/types";
import { Button } from "../components/Button";
import { DepartmentTree } from "../components/DepartmentTree";
import { EmptyState } from "../components/EmptyState";
import { Input } from "../components/Input";
import { Header } from "../layout/Header";
import { filterDepartmentTree, toSelectedDepartment } from "../utils/departments";
import { getErrorMessage } from "../api/http";

export function DepartmentsPage() {
  const [tree, setTree] = useState<DepartmentTreeItem[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState<SelectedDepartment | null>(
    getSelectedDepartment,
  );
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDepartments(): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      setTree(await getDepartmentsTree());
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDepartments();
  }, []);

  const filteredTree = useMemo(() => filterDepartmentTree(tree, search), [search, tree]);

  function handleSelect(node: DepartmentTreeItem): void {
    const nextSelectedDepartment = toSelectedDepartment(node);
    saveSelectedDepartment(nextSelectedDepartment);
    setSelectedDepartment(nextSelectedDepartment);
  }

  return (
    <section>
      <Header
        title="Departments"
        description="Выберите отделение для генерации SHPI. Выбор сохраняется в браузере."
        actions={
          <Button icon={<RefreshCw size={15} />} loading={loading} onClick={loadDepartments}>
            Обновить
          </Button>
        }
      />

      <div className="split-grid">
        <div className="panel">
          <Input
            label="Поиск"
            placeholder="Название, код или путь"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          {error ? <div className="alert alert-danger">{error}</div> : null}
          {loading ? <div className="inline-loader">Загрузка дерева...</div> : null}

          {!loading && filteredTree.length === 0 ? (
            <EmptyState
              title="Departments tree is empty"
              description="Проверьте импорт отделений или очистите поиск."
            />
          ) : null}

          {!loading && filteredTree.length > 0 ? (
            <DepartmentTree
              expandAll={search.trim().length > 0}
              nodes={filteredTree}
              selectedId={selectedDepartment?.id ?? null}
              onSelect={handleSelect}
            />
          ) : null}
        </div>

        <aside className="panel details-panel">
          <h2>Selected Department</h2>
          {selectedDepartment ? (
            <dl className="summary-list">
              <div>
                <dt>ID</dt>
                <dd>{selectedDepartment.id}</dd>
              </div>
              <div>
                <dt>Code</dt>
                <dd className="mono">{selectedDepartment.code}</dd>
              </div>
              <div>
                <dt>Name</dt>
                <dd>{selectedDepartment.name}</dd>
              </div>
              <div>
                <dt>Full path</dt>
                <dd>{selectedDepartment.full_path ?? "—"}</dd>
              </div>
            </dl>
          ) : (
            <EmptyState
              title="Отделение не выбрано"
              description="Кликните по узлу дерева, чтобы использовать department_id в Generate Barcode."
            />
          )}
        </aside>
      </div>
    </section>
  );
}
