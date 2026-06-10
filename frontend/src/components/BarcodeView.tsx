interface Props {
  code: string;
  caption?: string;
  height?: number;
  className?: string;
}

// Визуальное представление ШПИ: штрихи + моноширинный код.
// Всегда чёрное на белом, независимо от темы (раздел 4 брифа).
// Полоски декоративные; реальный сканируемый штрихкод печатает бэкенд в PDF.
export function BarcodeView({ code, caption, height = 48, className = '' }: Props) {
  return (
    <div className={`rounded-ctl border-[0.5px] border-bd3 bg-white p-3 text-center ${className}`}>
      {caption && <div className="mb-1.5 text-[13px] text-black">{caption}</div>}
      <div className="barcode-bars w-full" style={{ height }} />
      <div className="mt-1.5 font-mono text-[16px] tracking-[2px] text-black">{code}</div>
    </div>
  );
}
