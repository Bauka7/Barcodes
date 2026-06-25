import { useMemo, useState } from 'react';
import type { DepartmentTreeItem } from '../api/departments';

interface Props {
  nodes: DepartmentTreeItem[];
  selectedId?: number | null;
  onSelect?: (node: DepartmentTreeItem) => void;
  /** клиентский фильтр по имени/коду; совпадения автоматически раскрываются */
  filter?: string;
}

// Дерево отделений (архетип design-reference.html): раскрытие, выбор, поиск.
export function DepartmentTree({ nodes, selectedId, onSelect, filter }: Props) {
  const q = filter?.trim().toLowerCase() ?? '';
  const shown = useMemo(() => (q ? filterTree(nodes, q) : nodes), [nodes, q]);

  if (shown.length === 0) {
    return <div className="px-2 py-3 text-[16px] text-t3">—</div>;
  }

  return (
    <div className="text-[16px]">
      {shown.map((n) => (
        <TreeNode
          key={n.id}
          node={n}
          depth={0}
          selectedId={selectedId}
          onSelect={onSelect}
          forceOpen={!!q}
        />
      ))}
    </div>
  );
}

interface NodeProps {
  node: DepartmentTreeItem;
  depth: number;
  selectedId?: number | null;
  onSelect?: (node: DepartmentTreeItem) => void;
  forceOpen: boolean;
}

function TreeNode({ node, depth, selectedId, onSelect, forceOpen }: NodeProps) {
  const hasChildren = !!node.children?.length;
  const [open, setOpen] = useState(depth < 1 || forceOpen);
  const isOpen = open || forceOpen;
  const selected = selectedId === node.id;

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => onSelect?.(node)}
        className={`flex items-center justify-between rounded-ctl ${
          selected ? 'bg-brand-tint' : 'hover:bg-bg2'
        }`}
        style={{ paddingLeft: 8 + depth * 16 }}
      >
        <div className="flex min-w-0 items-center gap-1.5 py-1.5 pr-2">
          {hasChildren ? (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setOpen((o) => !o);
              }}
              className="text-t2"
              aria-label="toggle"
            >
              <i className={`ti ti-chevron-${isOpen ? 'down' : 'right'} text-[18px]`} />
            </button>
          ) : (
            <i className="ti ti-point text-[18px] text-t3" />
          )}
          <i
            className={`ti ${hasChildren ? 'ti-building-community' : 'ti-point'} ${
              selected ? 'text-brand-dark' : 'text-brand'
            }`}
          />
          <span className={`truncate ${selected ? 'text-brand-dark' : ''}`}>{node.name}</span>
          {node.department_type ? (
            <span className="rounded-full bg-bg2 px-1.5 py-0.5 text-[11px] uppercase tracking-wide text-t3">
              {node.department_type}
            </span>
          ) : null}
        </div>
        <span className="flex shrink-0 items-center gap-1 pr-2 font-mono text-[12px] text-t3">
          {node.shpi_region_code ? (
            <span
              className="rounded-full border border-bd3 bg-bg1 px-1.5 py-0.5 text-[11px] text-t2"
              title={node.shpi_region_name ?? undefined}
            >
              SHPI {node.shpi_region_code}
            </span>
          ) : null}
          <span>{node.code}</span>
        </span>
      </div>

      {hasChildren && isOpen && (
        <div>
          {node.children.map((c) => (
            <TreeNode
              key={c.id}
              node={c}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              forceOpen={forceOpen}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Оставляет узлы, где совпадает имя/код, либо есть совпадение в потомках.
function filterTree(nodes: DepartmentTreeItem[], q: string): DepartmentTreeItem[] {
  const res: DepartmentTreeItem[] = [];
  for (const n of nodes) {
    const kids = n.children?.length ? filterTree(n.children, q) : [];
    const self =
      n.name.toLowerCase().includes(q) ||
      n.code.toLowerCase().includes(q) ||
      (n.shpi_region_code ?? '').toLowerCase().includes(q);
    if (self || kids.length) {
      res.push({ ...n, children: kids.length ? kids : self ? (n.children ?? []) : [] });
    }
  }
  return res;
}
