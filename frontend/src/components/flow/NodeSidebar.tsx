import { MessageSquare, Box, CheckCircle, Wrench } from "lucide-react";
import type { NodeType } from "@/types/flow";

const nodeTypes: { type: NodeType; label: string; icon: React.ReactNode; color: string; desc: string }[] = [
  { type: "message", label: "Message", icon: <MessageSquare size={18} />, color: "bg-node-message", desc: "Send a text message" },
  { type: "entity", label: "Entity", icon: <Box size={18} />, color: "bg-node-entity", desc: "Collect user input" },
  { type: "confirmation", label: "Confirmation", icon: <CheckCircle size={18} />, color: "bg-node-confirmation", desc: "Yes/No question" },
  { type: "tool", label: "Tool", icon: <Wrench size={18} />, color: "bg-node-tool", desc: "Run an action" },
];

const NodeSidebar = () => {
  const onDragStart = (event: React.DragEvent, nodeType: NodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <aside className="w-60 bg-sidebar border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-sm font-semibold text-foreground tracking-wide uppercase">Nodes</h2>
        <p className="text-xs text-muted-foreground mt-1">Drag to canvas</p>
      </div>
      <div className="p-3 flex flex-col gap-2 flex-1 overflow-y-auto">
        {nodeTypes.map((node) => (
          <div
            key={node.type}
            className="flex items-center gap-3 p-3 rounded-lg bg-card border border-border cursor-grab hover:border-primary/50 transition-colors group"
            draggable
            onDragStart={(e) => onDragStart(e, node.type)}
          >
            <div className={`${node.color} text-white p-2 rounded-md flex-shrink-0`}>
              {node.icon}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground">{node.label}</p>
              <p className="text-xs text-muted-foreground">{node.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default NodeSidebar;
