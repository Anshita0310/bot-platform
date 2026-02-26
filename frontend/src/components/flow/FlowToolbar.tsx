import { Download, Trash2, Bot, PlayCircle, FileBox } from "lucide-react";

interface Props {
  onExportJSON: () => void;
  onClear: () => void;
  onTestFlow: () => void;
  onLoadExample: () => void;
}

const FlowToolbar = ({ onExportJSON, onClear, onTestFlow, onLoadExample }: Props) => {
  return (
    <header className="h-14 bg-sidebar border-b border-border flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <div className="bg-primary p-1.5 rounded-md">
          <Bot size={20} className="text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-foreground tracking-tight">Dialog Flow Builder</h1>
          <p className="text-[10px] text-muted-foreground">Design your bot conversation</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onLoadExample}
          className="flex items-center gap-2 px-3 py-1.5 bg-accent text-accent-foreground rounded-md text-xs font-medium hover:bg-accent/80 transition-colors"
        >
          <FileBox size={14} />
          Load Example
        </button>
        <button
          onClick={onTestFlow}
          className="flex items-center gap-2 px-3 py-1.5 bg-node-entity/20 text-node-entity border border-node-entity/30 rounded-md text-xs font-medium hover:bg-node-entity/30 transition-colors"
        >
          <PlayCircle size={14} />
          Test Flow
        </button>
        <button
          onClick={onExportJSON}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:bg-primary/90 transition-colors"
        >
          <Download size={14} />
          Export JSON
        </button>
        <button
          onClick={onClear}
          className="flex items-center gap-2 px-3 py-1.5 bg-destructive/10 text-destructive rounded-md text-xs font-medium hover:bg-destructive/20 transition-colors"
        >
          <Trash2 size={14} />
          Clear
        </button>
      </div>
    </header>
  );
};

export default FlowToolbar;
