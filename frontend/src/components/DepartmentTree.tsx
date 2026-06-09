import { Building2, ChevronDown, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";

import type { DepartmentTreeItem } from "../api/types";

interface DepartmentTreeProps {
  nodes: DepartmentTreeItem[];
  selectedId: number | null;
  onSelect: (node: DepartmentTreeItem) => void;
  expandAll?: boolean;
}

interface DepartmentNodeProps {
  node: DepartmentTreeItem;
  level: number;
  selectedId: number | null;
  onSelect: (node: DepartmentTreeItem) => void;
  expandAll: boolean;
}

function DepartmentNode({ expandAll, level, node, onSelect, selectedId }: DepartmentNodeProps) {
  const [isOpen, setIsOpen] = useState(level < 1);
  const hasChildren = node.children.length > 0;
  const selected = selectedId === node.id;

  useEffect(() => {
    if (expandAll) {
      setIsOpen(true);
    }
  }, [expandAll]);

  return (
    <li>
      <div
        className={`tree-row${selected ? " selected" : ""}`}
        style={{ paddingLeft: `${8 + level * 18}px` }}
      >
        <button
          aria-label={isOpen ? "Collapse" : "Expand"}
          className="tree-toggle"
          disabled={!hasChildren}
          type="button"
          onClick={() => setIsOpen((current) => !current)}
        >
          {hasChildren ? (
            isOpen ? (
              <ChevronDown size={15} />
            ) : (
              <ChevronRight size={15} />
            )
          ) : (
            <span className="tree-spacer" />
          )}
        </button>

        <button className="tree-node-button" type="button" onClick={() => onSelect(node)}>
          <Building2 size={15} />
          <span className="tree-node-text">
            <span>{node.name}</span>
            <span className="tree-node-meta">{node.code}</span>
          </span>
        </button>
      </div>

      {hasChildren && isOpen ? (
        <ul>
          {node.children.map((child) => (
            <DepartmentNode
              expandAll={expandAll}
              key={child.id}
              level={level + 1}
              node={child}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function DepartmentTree({
  expandAll = false,
  nodes,
  onSelect,
  selectedId,
}: DepartmentTreeProps) {
  return (
    <div className="tree-panel">
      <ul className="department-tree">
        {nodes.map((node) => (
          <DepartmentNode
            expandAll={expandAll}
            key={node.id}
            level={0}
            node={node}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        ))}
      </ul>
    </div>
  );
}
