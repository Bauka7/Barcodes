import type { SelectHTMLAttributes } from "react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
}

export function Select({ children, className = "", id, label, ...props }: SelectProps) {
  const selectId = id ?? props.name;

  return (
    <label className={`field ${className}`.trim()} htmlFor={selectId}>
      {label ? <span className="field-label">{label}</span> : null}
      <select id={selectId} {...props}>
        {children}
      </select>
    </label>
  );
}
