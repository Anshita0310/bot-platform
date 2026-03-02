import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { flowsApi, type FlowSummary } from "@/lib/api";
import { Bot, Plus, Trash2, LogOut, Clock } from "lucide-react";
import { toast } from "sonner";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [flows, setFlows] = useState<FlowSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFlows = useCallback(async () => {
    try {
      const data = await flowsApi.list();
      setFlows(data);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to load flows");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFlows();
  }, [fetchFlows]);

  const handleCreate = async () => {
    try {
      const startNode = {
        id: "node_start",
        type: "start",
        data: { type: "start", label: "Start" },
        position: { x: 250, y: 0 },
      };
      const endNode = {
        id: "node_end",
        type: "end",
        data: { type: "end", label: "End" },
        position: { x: 250, y: 400 },
      };
      const flow = await flowsApi.create({
        orgId: user?.orgId || "",
        projectId: "default",
        name: `Untitled Flow ${flows.length + 1}`,
        nodes: [startNode, endNode],
        edges: [],
      });
      navigate(`/flows/${flow._id}`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to create flow");
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await flowsApi.delete(id);
      setFlows((prev) => prev.filter((f) => f._id !== id));
      toast.success("Flow deleted");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to delete flow");
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="h-14 bg-sidebar border-b border-border flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="bg-primary p-1.5 rounded-md">
            <Bot size={20} className="text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-foreground tracking-tight">Bot Builder</h1>
            <p className="text-[10px] text-muted-foreground">{user?.orgId}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">{user?.email}</span>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Dialog Flows</h2>
            <p className="text-sm text-muted-foreground">Create and manage your bot dialog flows</p>
          </div>
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <Plus size={16} />
            New Flow
          </button>
        </div>

        {loading ? (
          <div className="text-center py-16 text-muted-foreground text-sm">Loading...</div>
        ) : flows.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-border rounded-xl">
            <Bot size={40} className="mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">No flows yet. Create your first one!</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {flows.map((flow) => (
              <div
                key={flow._id}
                className="flex items-center justify-between bg-card border border-border rounded-lg px-5 py-4 hover:border-primary/40 transition-colors cursor-pointer group"
                onClick={() => navigate(`/flows/${flow._id}`)}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-foreground truncate">{flow.name}</h3>
                    {flow.isDraft ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-node-confirmation/20 text-node-confirmation font-medium">
                        Draft
                      </span>
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-node-entity/20 text-node-entity font-medium">
                        v{flow.version}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>{flow.nodes.length} nodes</span>
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {new Date(flow.updatedAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(flow._id, flow.name);
                  }}
                  className="p-2 text-muted-foreground hover:text-destructive rounded-md hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
