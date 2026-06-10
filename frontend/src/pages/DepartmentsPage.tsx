import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDepartmentTree } from '../lib/departmentName';
import { DepartmentTree } from '../components/DepartmentTree';
import { ErrorText, Input, Loading, PageHeader } from '../components/ui';

export default function DepartmentsPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, error } = useDepartmentTree();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <div>
      <PageHeader title={t('departments.title')} subtitle={t('departments.subtitle')} />

      <div className="max-w-xl">
        <Input
          className="mb-3"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('departments.search')}
        />

        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorText error={error} />
        ) : (
          <div className="rounded-ctl border-[0.5px] border-bd3 p-2">
            <DepartmentTree
              nodes={data ?? []}
              filter={search}
              selectedId={selected}
              onSelect={(n) => setSelected(n.id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
