import type { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  align?: 'left' | 'right';
  /** доп. классы ячейки td */
  cellClassName?: string;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  rowClassName?: (row: T) => string;
  empty?: ReactNode;
  loading?: boolean;
  containerClassName?: string;
  tableClassName?: string;
}

const alignCls = (align?: 'left' | 'right') => (align === 'right' ? 'text-right' : 'text-left');

// Универсальная таблица-список (архетип design-reference.html).
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  rowClassName,
  empty,
  loading,
  containerClassName,
  tableClassName,
}: Props<T>) {
  return (
    <div className={`overflow-x-auto overflow-y-visible rounded-ctl border-[0.5px] border-bd3 ${containerClassName ?? ''}`}>
      <table className={`min-w-full border-collapse text-[16px] ${tableClassName ?? ''}`}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={`bg-bg2 px-3 py-2 text-[15px] font-normal text-t2 ${alignCls(c.align)}`}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-6 text-center text-t2">
                …
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-6 text-center text-t3">
                {empty ?? '—'}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`border-t-[0.5px] border-bd3 transition-colors ${
                  onRowClick ? 'cursor-pointer hover:bg-bg2' : 'hover:bg-bg2'
                } ${rowClassName?.(row) ?? ''}`}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={`px-3 py-2.5 align-middle ${alignCls(c.align)} ${c.cellClassName ?? ''}`}
                  >
                    {c.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
