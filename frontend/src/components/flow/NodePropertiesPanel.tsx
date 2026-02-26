import { useCallback } from "react";
import type { Node } from "@xyflow/react";
import type { FlowNodeData } from "@/types/flow";
import { X } from "lucide-react";

interface Props {
  node: Node;
  onChange: (id: string, data: FlowNodeData) => void;
  onClose: () => void;
}

const NodePropertiesPanel = ({ node, onChange, onClose }: Props) => {
  const data = node.data as unknown as FlowNodeData;

  const update = useCallback(
    (partial: Partial<FlowNodeData>) => {
      onChange(node.id, { ...data, ...partial } as FlowNodeData);
    },
    [node.id, data, onChange]
  );

  const inputClass = "w-full bg-muted border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary";
  const labelClass = "text-xs font-medium text-muted-foreground uppercase tracking-wide";

  return (
    <aside className="w-72 bg-sidebar border-l border-border flex flex-col">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Properties</h3>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X size={16} />
        </button>
      </div>
      <div className="p-4 space-y-4 flex-1 overflow-y-auto">
        <div>
          <label className={labelClass}>Label</label>
          <input className={inputClass} value={data.label} onChange={(e) => update({ label: e.target.value })} />
        </div>

        {data.type === "message" && (
          <div>
            <label className={labelClass}>Message Text</label>
            <textarea className={`${inputClass} min-h-[80px] resize-y`} value={data.message} onChange={(e) => update({ message: e.target.value })} placeholder="Enter bot message..." />
          </div>
        )}

        {data.type === "entity" && (
          <>
            <div>
              <label className={labelClass}>Entity Name</label>
              <input className={inputClass} value={data.entityName} onChange={(e) => update({ entityName: e.target.value })} placeholder="e.g. user_name" />
            </div>
            <div>
              <label className={labelClass}>Entity Type</label>
              <select className={inputClass} value={data.entityType} onChange={(e) => update({ entityType: e.target.value })}>
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="email">Email</option>
                <option value="phone">Phone</option>
                <option value="date">Date</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Prompt</label>
              <textarea className={`${inputClass} min-h-[60px] resize-y`} value={data.prompt} onChange={(e) => update({ prompt: e.target.value })} placeholder="What to ask the user..." />
            </div>
          </>
        )}

        {data.type === "confirmation" && (
          <>
            <div>
              <label className={labelClass}>Question</label>
              <textarea className={`${inputClass} min-h-[60px] resize-y`} value={data.question} onChange={(e) => update({ question: e.target.value })} placeholder="Confirmation question..." />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelClass}>Yes Label</label>
                <input className={inputClass} value={data.yesLabel} onChange={(e) => update({ yesLabel: e.target.value })} />
              </div>
              <div>
                <label className={labelClass}>No Label</label>
                <input className={inputClass} value={data.noLabel} onChange={(e) => update({ noLabel: e.target.value })} />
              </div>
            </div>
          </>
        )}

        {data.type === "tool" && (
          <>
            <div>
              <label className={labelClass}>Tool Name</label>
              <input className={inputClass} value={data.toolName} onChange={(e) => update({ toolName: e.target.value })} placeholder="e.g. api_call" />
            </div>
            <div>
              <label className={labelClass}>Description</label>
              <textarea className={`${inputClass} min-h-[60px] resize-y`} value={data.description} onChange={(e) => update({ description: e.target.value })} placeholder="What this tool does..." />
            </div>
          </>
        )}
      </div>
    </aside>
  );
};

export default NodePropertiesPanel;
