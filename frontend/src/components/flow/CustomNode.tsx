import { memo, useState } from "react";
import { Handle, Position, type NodeProps, useReactFlow } from "@xyflow/react";
import { MessageSquare, Box, CheckCircle, Wrench, Pencil, X, Check, Trash2, Play, Square } from "lucide-react";
import type { FlowNodeData } from "@/types/flow";

const nodeConfig = {
  start: { icon: <Play size={16} />, color: "border-node-entity", bgAccent: "bg-node-entity/10", headerBg: "bg-node-entity", label: "Start" },
  end: { icon: <Square size={16} />, color: "border-destructive", bgAccent: "bg-destructive/10", headerBg: "bg-destructive", label: "End" },
  message: { icon: <MessageSquare size={16} />, color: "border-node-message", bgAccent: "bg-node-message/10", headerBg: "bg-node-message", label: "Message" },
  entity: { icon: <Box size={16} />, color: "border-node-entity", bgAccent: "bg-node-entity/10", headerBg: "bg-node-entity", label: "Entity" },
  confirmation: { icon: <CheckCircle size={16} />, color: "border-node-confirmation", bgAccent: "bg-node-confirmation/10", headerBg: "bg-node-confirmation", label: "Confirmation" },
  tool: { icon: <Wrench size={16} />, color: "border-node-tool", bgAccent: "bg-node-tool/10", headerBg: "bg-node-tool", label: "Tool" },
};

const CustomNode = ({ data, id }: NodeProps) => {
  const nodeData = data as unknown as FlowNodeData;
  const config = nodeConfig[nodeData.type];
  const [editing, setEditing] = useState(false);
  const [editLabel, setEditLabel] = useState(nodeData.label);
  const { deleteElements } = useReactFlow();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteElements({ nodes: [{ id }] });
  };

  const handleSaveLabel = () => {
    nodeData.label = editLabel;
    setEditing(false);
  };

  return (
    <div className={`min-w-[200px] max-w-[260px] rounded-lg border-2 ${config.color} bg-card shadow-lg`}>
      {nodeData.type !== "start" && <Handle type="target" position={Position.Top} className="!w-3 !h-3" />}

      {/* Header */}
      <div className={`${config.headerBg} text-white px-3 py-2 rounded-t-[6px] flex items-center gap-2`}>
        {config.icon}
        {editing ? (
          <div className="flex items-center gap-1 flex-1">
            <input
              className="bg-white/20 text-white text-xs rounded px-1.5 py-0.5 flex-1 outline-none placeholder:text-white/50"
              value={editLabel}
              onChange={(e) => setEditLabel(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSaveLabel()}
              autoFocus
            />
            <button onClick={handleSaveLabel} className="hover:bg-white/20 rounded p-0.5">
              <Check size={12} />
            </button>
            <button onClick={() => setEditing(false)} className="hover:bg-white/20 rounded p-0.5">
              <X size={12} />
            </button>
          </div>
        ) : (
          <>
            <span className="text-xs font-semibold flex-1 truncate">{nodeData.label}</span>
            <button onClick={() => setEditing(true)} className="hover:bg-white/20 rounded p-0.5 opacity-60 hover:opacity-100">
              <Pencil size={12} />
            </button>
            <button onClick={handleDelete} className="hover:bg-white/20 rounded p-0.5 opacity-60 hover:opacity-100 text-red-200 hover:text-red-100">
              <Trash2 size={12} />
            </button>
          </>
        )}
      </div>

      {/* Body */}
      <div className={`px-3 py-2.5 text-xs space-y-1.5 ${config.bgAccent}`}>
        {(nodeData.type === "start" || nodeData.type === "end") && (
          <div className="text-muted-foreground text-center py-1">
            {nodeData.type === "start" ? "Flow begins here" : "Flow ends here"}
          </div>
        )}
        {nodeData.type === "message" && (
          <div>
            <span className="text-muted-foreground">Message:</span>
            <p className="text-foreground mt-0.5">{nodeData.message || "—"}</p>
          </div>
        )}
        {nodeData.type === "entity" && (
          <>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Name:</span>
              <span className="text-foreground">{nodeData.entityName || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Type:</span>
              <span className="text-foreground">{nodeData.entityType || "—"}</span>
            </div>
          </>
        )}
        {nodeData.type === "confirmation" && (
          <div>
            <span className="text-muted-foreground">Question:</span>
            <p className="text-foreground mt-0.5">{nodeData.question || "—"}</p>
          </div>
        )}
        {nodeData.type === "tool" && (
          <>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tool:</span>
              <span className="text-foreground">{nodeData.toolName || "—"}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Desc:</span>
              <p className="text-foreground mt-0.5">{nodeData.description || "—"}</p>
            </div>
          </>
        )}
      </div>

      {nodeData.type !== "end" && <Handle type="source" position={Position.Bottom} className="!w-3 !h-3" />}
      {nodeData.type === "confirmation" && (
        <>
          <Handle type="source" position={Position.Right} id="yes" className="!w-3 !h-3 !bg-node-entity !border-node-entity" style={{ top: '60%' }} />
          <Handle type="source" position={Position.Left} id="no" className="!w-3 !h-3 !bg-destructive !border-destructive" style={{ top: '60%' }} />
        </>
      )}
    </div>
  );
};

export default memo(CustomNode);
