import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getShpiMap, type ShpiMapCodeItem, type ShpiMapStatus } from '../api/shpiMap';
import { ErrorText, PageHeader } from '../components/ui';

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

function LegendItem({ status }: { status: ShpiMapStatus }) {
  const { t } = useTranslation();

  return (
    <span className="inline-flex items-center gap-2">
      <span className={`h-3 w-3 rounded-[2px] ${STATUS_DOT_CLASS[status]}`} />
      {t(`shpiMap.status.${status}`)}
    </span>
  );
}

function buildCellMap(cells: ShpiMapCodeItem[]) {
  const map = new Map<string, ShpiMapCodeItem>();
  for (const cell of cells) {
    map.set(`${cell.code}:${cell.region_code}`, cell);
  }
  return map;
}

export default function ShpiMapPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['shpi-map'],
    queryFn: getShpiMap,
  });

  const regionCodes = data?.region_codes ?? [];
  const regionByCode = new Map((data?.regions ?? []).map((region) => [region.code, region]));
  const codes = data?.codes ?? [];
  const cellMap = buildCellMap(data?.cells ?? []);

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

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <div className="overflow-auto rounded-ctl border-[0.5px] border-bd3">
          <table className="min-w-full border-collapse text-[15px]">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-bg2 px-3 py-2 text-left font-normal text-t2">
                  {t('shpiMap.code')}
                </th>
                {regionCodes.map((regionCode) => (
                  <th
                    key={regionCode}
                    className="bg-bg2 px-3 py-2 text-right font-normal text-t2"
                    title={regionByCode.get(regionCode)?.name ?? regionCode}
                  >
                    {regionCode}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={regionCodes.length + 1} className="px-3 py-6 text-center text-t2">
                    ...
                  </td>
                </tr>
              ) : codes.length === 0 ? (
                <tr>
                  <td colSpan={regionCodes.length + 1} className="px-3 py-6 text-center text-t3">
                    {t('shpiMap.empty')}
                  </td>
                </tr>
              ) : (
                codes.map((code) => (
                  <tr key={code} className="border-t-[0.5px] border-bd3">
                    <td className="sticky left-0 z-10 bg-bg1 px-3 py-2.5 align-middle font-mono font-medium">
                      {code}
                    </td>
                    {regionCodes.map((regionCode) => {
                      const cell = cellMap.get(`${code}:${regionCode}`);
                      const status = cell?.status ?? 'gray';
                      const currentValue = cell?.current_value ?? 0;

                      return (
                        <td
                          key={regionCode}
                          className={`px-3 py-2.5 text-right align-middle font-mono ${STATUS_CELL_CLASS[status]}`}
                        >
                          {currentValue.toLocaleString('ru-RU')}
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
  );
}
