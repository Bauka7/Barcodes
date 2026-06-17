import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import {
  importFilPassportDepartments,
  type FilPassportDepartmentImportResponse,
} from '../api/departments';
import { useDepartmentTree } from '../lib/departmentName';
import { DepartmentTree } from '../components/DepartmentTree';
import { Button, ErrorText, Input, Loading, PageHeader } from '../components/ui';

export default function DepartmentsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error } = useDepartmentTree();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<number | null>(null);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<unknown>(null);
  const [importResult, setImportResult] = useState<FilPassportDepartmentImportResponse | null>(null);

  const runFilPassportImport = async () => {
    const confirmed = window.confirm(
      t('departments.importConfirm', {
        defaultValue: 'Импортировать официальные отделения из FilPassport?',
      }),
    );
    if (!confirmed) return;

    setImporting(true);
    setImportError(null);
    setImportResult(null);
    try {
      const result = await importFilPassportDepartments(false);
      setImportResult(result);
      await queryClient.invalidateQueries({ queryKey: ['departments', 'tree'] });
      await queryClient.invalidateQueries({ queryKey: ['departments'] });
    } catch (err) {
      setImportError(err);
    } finally {
      setImporting(false);
    }
  };

  const hasImportWarnings = Boolean(importResult?.errors.length);

  return (
    <div>
      <PageHeader
        title={t('departments.title')}
        subtitle={t('departments.subtitle')}
        actions={
          user?.role === 'admin' ? (
            <Button onClick={runFilPassportImport} disabled={importing}>
              <i className="ti ti-cloud-download" />
              {importing
                ? t('common.loading')
                : t('departments.importFilPassport', {
                    defaultValue: 'Импортировать из FilPassport',
                  })}
            </Button>
          ) : null
        }
      />

      <div className="max-w-xl">
        {importError ? <div className="mb-3"><ErrorText error={importError} /></div> : null}
        {importResult ? (
          <div
            className={`mb-3 rounded-ctl border-[0.5px] px-3 py-2 text-[15px] ${
              hasImportWarnings
                ? 'border-amber-200 bg-amber-50 text-amber-900'
                : 'border-bd3 bg-bg2 text-t2'
            }`}
          >
            <div className="font-medium text-t1">
              {hasImportWarnings
                ? t('departments.importDoneWithWarnings', {
                    defaultValue: 'Импорт завершён с предупреждениями',
                  })
                : t('departments.importDone', { defaultValue: 'Импорт завершён' })}
            </div>
            <div>
              {t('departments.importSummary', {
                defaultValue:
                  'Создано: {{created}}, обновлено: {{updated}}, пропущено: {{skipped}}, отсутствует в источнике: {{missing}}',
                created: importResult.created,
                updated: importResult.updated,
                skipped: importResult.skipped,
                missing: importResult.missing,
              })}
            </div>
            {hasImportWarnings ? (
              <div className="mt-2">
                <div className="font-medium">
                  {t('departments.importErrors', {
                    defaultValue: 'Ошибки / предупреждения: {{count}}',
                    count: importResult.errors.length,
                  })}
                </div>
                <ol className="mt-1 list-decimal space-y-1 pl-5">
                  {importResult.errors.map((message, index) => (
                    <li key={`${index}-${message}`}>{message}</li>
                  ))}
                </ol>
              </div>
            ) : null}
          </div>
        ) : null}
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
