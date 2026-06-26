import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { ApiError } from '../api/client';
import {
  getOfficialShpiCounters,
  getShpiMap,
  type OfficialShpiCounterItem,
  type ShpiMapCodeItem,
  type ShpiMapStatus,
} from '../api/shpiMap';
import { Chip, type ChipTone } from '../components/Chip';
import { Button, Card, ErrorText, Field, Input, PageHeader, Select } from '../components/ui';

const OFFICIAL_REGION_CODES = [
  '01',
  '02',
  '03',
  '04',
  '05',
  '06',
  '07',
  '08',
  '09',
  '10',
  '11',
  '12',
  '13',
  '14',
  '15',
  '16',
  '17',
  '18',
  '19',
  '20',
  '30',
  '34',
];

const STATUS_CELL_CLASS: Record<ShpiMapStatus, string> = {
  green: 'bg-green-100 text-green-950',
  gray: 'bg-zinc-100 text-zinc-800',
  red: 'bg-red-100 text-red-950',
};

const STATUS_DOT_CLASS: Record<ShpiMapStatus, string> = {
  green: 'bg-green-500',
  gray: 'bg-zinc-300',
  red: 'bg-red-500',
};

type TabKey = 'officialMap' | 'officialDetails' | 'source' | 'localDiagnostic';
type OfficialCounterStatus = 'active' | 'exhausted' | 'empty';

const OFFICIAL_STATUS_TONE: Record<OfficialCounterStatus, ChipTone> = {
  active: 'ok',
  exhausted: 'bad',
  empty: 'muted',
};

const OFFICIAL_STATUS_TO_CELL: Record<OfficialCounterStatus, ShpiMapStatus> = {
  active: 'green',
  exhausted: 'red',
  empty: 'gray',
};

function LegendItem({ status }: { status: ShpiMapStatus }) {
  const { t } = useTranslation();

  return (
    <span className="inline-flex items-center gap-2">
      <span className={`h-3 w-3 rounded-[2px] ${STATUS_DOT_CLASS[status]}`} />
      {t(`shpiMap.status.${status}`)}
    </span>
  );
}

function buildLocalCellMap(cells: ShpiMapCodeItem[]) {
  const map = new Map<string, ShpiMapCodeItem>();
  for (const cell of cells) {
    map.set(`${cell.code}:${cell.region_code}`, cell);
  }
  return map;
}

function buildOfficialCounterMap(counters: OfficialShpiCounterItem[]) {
  const map = new Map<string, OfficialShpiCounterItem>();
  for (const counter of counters) {
    map.set(`${counter.package_type}:${counter.region_code}`, counter);
  }
  return map;
}

function getCurrentValueStatus(currentValue: number): OfficialCounterStatus {
  if (currentValue >= 999999) return 'exhausted';
  if (currentValue > 0) return 'active';
  return 'empty';
}

function getOfficialStatus(counter: OfficialShpiCounterItem): OfficialCounterStatus {
  return getCurrentValueStatus(counter.current_value);
}

function formatNumber(value: number) {
  return value.toLocaleString('ru-RU');
}

function formatDate(value: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function getOfficialErrorMessage(error: unknown, t: (key: string) => string) {
  if (error instanceof ApiError) {
    const detail = typeof error.detail === 'string' ? error.detail : error.message;
    const normalized = detail.toLowerCase();

    if (error.status === 403) return t('shpiMap.official.errors.forbidden');
    if (normalized.includes('disabled')) return t('shpiMap.official.errors.disabled');
    if (error.status === 503) return t('shpiMap.official.errors.unavailable');
  }

  return t('shpiMap.official.errors.generic');
}

function buildOfficialCellTitle(
  packageType: string,
  regionCode: string,
  counter: OfficialShpiCounterItem | undefined,
) {
  return [
    `package_type: ${packageType}`,
    `region_code: ${regionCode}`,
    `current_value: ${formatNumber(counter?.current_value ?? 0)}`,
    `used_count: ${formatNumber(counter?.used_count ?? 0)}`,
    `last_used_date: ${formatDate(counter?.last_used_date ?? null)}`,
  ].join('\n');
}

export default function ShpiMapPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabKey>('officialMap');
  const [packageFilter, setPackageFilter] = useState('');
  const [regionFilter, setRegionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | OfficialCounterStatus>('all');

  const localMapQuery = useQuery({
    queryKey: ['shpi-map'],
    queryFn: getShpiMap,
    enabled: activeTab === 'localDiagnostic',
  });
  const officialQuery = useQuery({
    queryKey: ['official-shpi-counters'],
    queryFn: getOfficialShpiCounters,
  });

  const localRegionCodes = localMapQuery.data?.region_codes ?? [];
  const localRegionByCode = new Map(
    (localMapQuery.data?.regions ?? []).map((region) => [region.code, region]),
  );
  const localCodes = localMapQuery.data?.codes ?? [];
  const localCellMap = buildLocalCellMap(localMapQuery.data?.cells ?? []);

  const officialCounters = officialQuery.data ?? [];
  const officialCounterMap = useMemo(
    () => buildOfficialCounterMap(officialCounters),
    [officialCounters],
  );
  const packageTypes = useMemo(
    () => Array.from(new Set(officialCounters.map((item) => item.package_type))).sort(),
    [officialCounters],
  );
  const officialRegionCodes = useMemo(
    () => Array.from(new Set(officialCounters.map((item) => item.region_code))).sort(),
    [officialCounters],
  );
  const filteredOfficialCounters = useMemo(
    () =>
      officialCounters.filter((item) => {
        const status = getOfficialStatus(item);
        return (
          (!packageFilter || item.package_type.includes(packageFilter.trim().toUpperCase())) &&
          (!regionFilter || item.region_code === regionFilter) &&
          (statusFilter === 'all' || status === statusFilter)
        );
      }),
    [officialCounters, packageFilter, regionFilter, statusFilter],
  );
  const officialSummary = useMemo(() => {
    const statuses = officialCounters.map(getOfficialStatus);
    return {
      total: officialCounters.length,
      packageTypes: packageTypes.length,
      regionCodes: officialRegionCodes.length,
      active: statuses.filter((status) => status === 'active').length,
      exhausted: statuses.filter((status) => status === 'exhausted').length,
    };
  }, [officialCounters, packageTypes.length, officialRegionCodes.length]);

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'officialMap', label: t('shpiMap.tabs.officialMap') },
    { key: 'officialDetails', label: t('shpiMap.tabs.officialDetails') },
    { key: 'source', label: t('shpiMap.tabs.source') },
    { key: 'localDiagnostic', label: t('shpiMap.tabs.localDiagnostic') },
  ];

  const officialError = officialQuery.isError
    ? getOfficialErrorMessage(officialQuery.error, t)
    : null;

  return (
    <div>
      <PageHeader
        title={t('shpiMap.title')}
        subtitle={t('shpiMap.subtitle')}
        actions={
          <div className="flex flex-wrap items-center gap-3 text-[15px] text-t2">
            <LegendItem status="green" />
            <LegendItem status="gray" />
            <LegendItem status="red" />
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <Button
            key={tab.key}
            type="button"
            variant={activeTab === tab.key ? 'primary' : 'default'}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {activeTab === 'officialMap' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[15px] text-t2">{t('shpiMap.officialMap.note')}</p>
            <Button
              type="button"
              onClick={() => void officialQuery.refetch()}
              disabled={officialQuery.isFetching}
            >
              {officialQuery.isFetching
                ? t('shpiMap.official.refreshing')
                : t('shpiMap.official.refresh')}
            </Button>
          </div>

          {officialError ? (
            <ErrorText error={officialError} />
          ) : (
            <div className="overflow-auto rounded-ctl border-[0.5px] border-bd3">
              <table className="min-w-full border-collapse text-[15px]">
                <thead>
                  <tr>
                    <th className="sticky left-0 z-10 bg-bg2 px-3 py-2 text-left font-normal text-t2">
                      {t('shpiMap.official.columns.packageType')}
                    </th>
                    {OFFICIAL_REGION_CODES.map((regionCode) => (
                      <th key={regionCode} className="bg-bg2 px-3 py-2 text-right font-normal text-t2">
                        {regionCode}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {officialQuery.isLoading ? (
                    <tr>
                      <td
                        colSpan={OFFICIAL_REGION_CODES.length + 1}
                        className="px-3 py-6 text-center text-t2"
                      >
                        ...
                      </td>
                    </tr>
                  ) : packageTypes.length === 0 ? (
                    <tr>
                      <td
                        colSpan={OFFICIAL_REGION_CODES.length + 1}
                        className="px-3 py-6 text-center text-t3"
                      >
                        {t('shpiMap.official.empty')}
                      </td>
                    </tr>
                  ) : (
                    packageTypes.map((packageType) => (
                      <tr key={packageType} className="border-t-[0.5px] border-bd3">
                        <td className="sticky left-0 z-10 bg-bg1 px-3 py-2.5 align-middle font-mono font-medium">
                          {packageType}
                        </td>
                        {OFFICIAL_REGION_CODES.map((regionCode) => {
                          const counter = officialCounterMap.get(`${packageType}:${regionCode}`);
                          const currentValue = counter?.current_value ?? 0;
                          const status = getCurrentValueStatus(currentValue);
                          const cellStatus = OFFICIAL_STATUS_TO_CELL[status];

                          return (
                            <td
                              key={regionCode}
                              className={`px-3 py-2.5 text-right align-middle font-mono ${STATUS_CELL_CLASS[cellStatus]}`}
                              title={buildOfficialCellTitle(packageType, regionCode, counter)}
                            >
                              {formatNumber(currentValue)}
                            </td>
                          );
                        })}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'officialDetails' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div className="grid flex-1 grid-cols-1 gap-3 md:grid-cols-3">
              <Field label={t('shpiMap.official.filters.packageType')} className="mb-0">
                <Input
                  value={packageFilter}
                  onChange={(event) => setPackageFilter(event.target.value)}
                  placeholder="AP"
                />
              </Field>
              <Field label={t('shpiMap.official.filters.regionCode')} className="mb-0">
                <Select value={regionFilter} onChange={(event) => setRegionFilter(event.target.value)}>
                  <option value="">{t('shpiMap.official.filters.allRegions')}</option>
                  {officialRegionCodes.map((regionCode) => (
                    <option key={regionCode} value={regionCode}>
                      {regionCode}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label={t('shpiMap.official.filters.status')} className="mb-0">
                <Select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as 'all' | OfficialCounterStatus)}
                >
                  <option value="all">{t('shpiMap.official.filters.allStatuses')}</option>
                  <option value="active">{t('shpiMap.official.status.active')}</option>
                  <option value="exhausted">{t('shpiMap.official.status.exhausted')}</option>
                  <option value="empty">{t('shpiMap.official.status.empty')}</option>
                </Select>
              </Field>
            </div>
            <Button
              type="button"
              onClick={() => void officialQuery.refetch()}
              disabled={officialQuery.isFetching}
            >
              {officialQuery.isFetching
                ? t('shpiMap.official.refreshing')
                : t('shpiMap.official.refresh')}
            </Button>
          </div>

          {officialError && <ErrorText error={officialError} />}

          {!officialError && (
            <>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
                <Card>
                  <div className="text-[13px] text-t2">{t('shpiMap.official.summary.total')}</div>
                  <div className="mt-1 text-2xl font-medium">{formatNumber(officialSummary.total)}</div>
                </Card>
                <Card>
                  <div className="text-[13px] text-t2">{t('shpiMap.official.summary.packageTypes')}</div>
                  <div className="mt-1 text-2xl font-medium">{formatNumber(officialSummary.packageTypes)}</div>
                </Card>
                <Card>
                  <div className="text-[13px] text-t2">{t('shpiMap.official.summary.regionCodes')}</div>
                  <div className="mt-1 text-2xl font-medium">{formatNumber(officialSummary.regionCodes)}</div>
                </Card>
                <Card>
                  <div className="text-[13px] text-t2">{t('shpiMap.official.summary.active')}</div>
                  <div className="mt-1 text-2xl font-medium">{formatNumber(officialSummary.active)}</div>
                </Card>
                <Card>
                  <div className="text-[13px] text-t2">{t('shpiMap.official.summary.exhausted')}</div>
                  <div className="mt-1 text-2xl font-medium">{formatNumber(officialSummary.exhausted)}</div>
                </Card>
              </div>

              <div className="overflow-auto rounded-ctl border-[0.5px] border-bd3">
                <table className="min-w-full border-collapse text-[15px]">
                  <thead>
                    <tr className="bg-bg2 text-left text-t2">
                      <th className="px-3 py-2 font-normal">{t('shpiMap.official.columns.packageType')}</th>
                      <th className="px-3 py-2 font-normal">{t('shpiMap.official.columns.regionCode')}</th>
                      <th className="px-3 py-2 text-right font-normal">{t('shpiMap.official.columns.currentValue')}</th>
                      <th className="px-3 py-2 text-right font-normal">{t('shpiMap.official.columns.usedCount')}</th>
                      <th className="px-3 py-2 font-normal">{t('shpiMap.official.columns.lastUsedDate')}</th>
                      <th className="px-3 py-2 font-normal">{t('shpiMap.official.columns.status')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {officialQuery.isLoading ? (
                      <tr>
                        <td colSpan={6} className="px-3 py-6 text-center text-t2">
                          ...
                        </td>
                      </tr>
                    ) : filteredOfficialCounters.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-3 py-6 text-center text-t3">
                          {t('shpiMap.official.empty')}
                        </td>
                      </tr>
                    ) : (
                      filteredOfficialCounters.map((counter) => {
                        const status = getOfficialStatus(counter);
                        return (
                          <tr
                            key={`${counter.package_type}:${counter.region_code}`}
                            className="border-t-[0.5px] border-bd3"
                          >
                            <td className="px-3 py-2.5 font-mono font-medium">{counter.package_type}</td>
                            <td className="px-3 py-2.5 font-mono">{counter.region_code}</td>
                            <td className="px-3 py-2.5 text-right font-mono">
                              {formatNumber(counter.current_value)}
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono">
                              {formatNumber(counter.used_count)}
                            </td>
                            <td className="px-3 py-2.5">{formatDate(counter.last_used_date)}</td>
                            <td className="px-3 py-2.5">
                              <Chip tone={OFFICIAL_STATUS_TONE[status]}>
                                {t(`shpiMap.official.status.${status}`)}
                              </Chip>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'source' && (
        <Card className="space-y-4">
          <div>
            <h3 className="text-xl font-medium">{t('shpiMap.source.title')}</h3>
            <p className="mt-1 text-[15px] text-t2">{t('shpiMap.source.note')}</p>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <div className="text-[13px] text-t2">{t('shpiMap.source.database')}</div>
              <div className="font-mono">toolpar</div>
            </div>
            <div>
              <div className="text-[13px] text-t2">{t('shpiMap.source.table')}</div>
              <div className="font-mono">public.a_mail</div>
            </div>
            <div>
              <div className="text-[13px] text-t2">{t('shpiMap.source.shpiColumn')}</div>
              <div className="font-mono">mail_id_</div>
            </div>
            <div>
              <div className="text-[13px] text-t2">{t('shpiMap.source.dateColumn')}</div>
              <div className="font-mono">mail_register_date_</div>
            </div>
          </div>
          <div className="rounded-ctl bg-bg2 p-3">
            <div className="mb-2 text-[13px] text-t2">{t('shpiMap.source.example')}</div>
            <div className="font-mono text-lg">AP061226515KZ</div>
            <ul className="mt-3 space-y-1 text-[15px] text-t2">
              <li>AP = package_type</li>
              <li>06 = region_code</li>
              <li>122651 = sequence_number</li>
              <li>5 = check_digit</li>
              <li>KZ = country</li>
            </ul>
          </div>
        </Card>
      )}

      {activeTab === 'localDiagnostic' && (
        <div className="space-y-4">
          <Card>
            <p className="text-[15px] text-t2">{t('shpiMap.localDiagnostic.note')}</p>
          </Card>

          {localMapQuery.isError ? (
            <ErrorText error={localMapQuery.error} />
          ) : (
            <div className="overflow-auto rounded-ctl border-[0.5px] border-bd3">
              <table className="min-w-full border-collapse text-[15px]">
                <thead>
                  <tr>
                    <th className="sticky left-0 z-10 bg-bg2 px-3 py-2 text-left font-normal text-t2">
                      {t('shpiMap.code')}
                    </th>
                    {localRegionCodes.map((regionCode) => (
                      <th
                        key={regionCode}
                        className="bg-bg2 px-3 py-2 text-right font-normal text-t2"
                        title={localRegionByCode.get(regionCode)?.name ?? regionCode}
                      >
                        {regionCode}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {localMapQuery.isLoading ? (
                    <tr>
                      <td colSpan={localRegionCodes.length + 1} className="px-3 py-6 text-center text-t2">
                        ...
                      </td>
                    </tr>
                  ) : localCodes.length === 0 ? (
                    <tr>
                      <td colSpan={localRegionCodes.length + 1} className="px-3 py-6 text-center text-t3">
                        {t('shpiMap.empty')}
                      </td>
                    </tr>
                  ) : (
                    localCodes.map((code) => (
                      <tr key={code} className="border-t-[0.5px] border-bd3">
                        <td className="sticky left-0 z-10 bg-bg1 px-3 py-2.5 align-middle font-mono font-medium">
                          {code}
                        </td>
                        {localRegionCodes.map((regionCode) => {
                          const cell = localCellMap.get(`${code}:${regionCode}`);
                          const status = cell?.status ?? 'gray';
                          const currentValue = cell?.current_value ?? 0;

                          return (
                            <td
                              key={regionCode}
                              className={`px-3 py-2.5 text-right align-middle font-mono ${STATUS_CELL_CLASS[status]}`}
                            >
                              {formatNumber(currentValue)}
                            </td>
                          );
                        })}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
