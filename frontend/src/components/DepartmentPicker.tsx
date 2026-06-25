import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { DepartmentTreeItem } from '../api/departments';
import { DepartmentTree } from './DepartmentTree';
import { Input } from './ui';

interface Props {
  nodes: DepartmentTreeItem[];
  value: number | null;
  onChange: (departmentId: number | null) => void;
  allowClear?: boolean;
  loading?: boolean;
}

function findDepartment(
  nodes: DepartmentTreeItem[],
  id: number | null,
): DepartmentTreeItem | null {
  if (id === null) return null;

  for (const node of nodes) {
    if (node.id === id) return node;
    const child = findDepartment(node.children ?? [], id);
    if (child) return child;
  }

  return null;
}

export function DepartmentPicker({
  nodes,
  value,
  onChange,
  allowClear = false,
  loading = false,
}: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const selected = useMemo(() => findDepartment(nodes, value), [nodes, value]);

  const selectDepartment = (node: DepartmentTreeItem) => {
    onChange(node.id);
    setOpen(false);
    setSearch('');
  };

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className={`flex min-h-10 w-full items-center justify-between gap-3 rounded-ctl border-[0.5px] bg-bg1 px-2.5 py-2 text-left text-[15px] ${
          open ? 'border-brand' : 'border-bd2'
        }`}
      >
        <span className="min-w-0">
          {selected ? (
            <>
              <span className="block truncate text-t1">{selected.name}</span>
              <span className="block truncate font-mono text-[12px] text-t3">
                {selected.full_path ?? selected.code}
                {selected.shpi_region_code ? ` — SHPI ${selected.shpi_region_code}` : ''}
              </span>
            </>
          ) : (
            <span className="text-t3">
              {loading ? t('common.loading') : t('users.departmentChoose')}
            </span>
          )}
        </span>
        <i className={`ti ti-chevron-${open ? 'up' : 'down'} shrink-0 text-[18px] text-t2`} />
      </button>

      {open && (
        <div className="mt-2 rounded-ctl border-[0.5px] border-bd2 bg-bg1 p-2">
          <div className="mb-2 flex gap-2">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t('users.departmentSearch')}
              autoFocus
            />
            {allowClear && value !== null && (
              <button
                type="button"
                onClick={() => {
                  onChange(null);
                  setOpen(false);
                  setSearch('');
                }}
                className="shrink-0 rounded-ctl border-[0.5px] border-bd2 px-2 text-t2 hover:bg-bg2 hover:text-t1"
                title={t('users.departmentClear')}
                aria-label={t('users.departmentClear')}
              >
                <i className="ti ti-x text-[18px]" />
              </button>
            )}
          </div>

          <div className="max-h-72 overflow-auto">
            <DepartmentTree
              nodes={nodes}
              filter={search}
              selectedId={value}
              onSelect={selectDepartment}
            />
          </div>
        </div>
      )}
    </div>
  );
}
