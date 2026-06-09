import type { TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({ className = "", id, label, ...props }: TextareaProps) {
  const textareaId = id ?? props.name;

  return (
    <label className={`field ${className}`.trim()} htmlFor={textareaId}>
      {label ? <span className="field-label">{label}</span> : null}
      <textarea id={textareaId} {...props} />
    </label>
  );
}
