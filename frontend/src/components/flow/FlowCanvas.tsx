import { useCallback, useRef, useState, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  type Node,
  BackgroundVariant,
  type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import CustomNode from "./CustomNode";
import EdgeConditionLabel from "./EdgeConditionLabel";
import NodeSidebar from "./NodeSidebar";
import FlowToolbar from "./FlowToolbar";
import NodePropertiesPanel from "./NodePropertiesPanel";
import ChatTestPanel from "./ChatTestPanel";
import type { FlowNodeData, NodeType } from "@/types/flow";
import { flowsApi } from "@/lib/api";
import { toast } from "sonner";

const nodeTypes = {
  custom: CustomNode,
};

const edgeTypes = {
  condition: EdgeConditionLabel,
};

let nodeId = 0;
const getNodeId = () => `node_${++nodeId}`;

const defaultDataForType = (type: NodeType): FlowNodeData => {
  switch (type) {
    case "start":
      return { type: "start", label: "Start" };
    case "end":
      return { type: "end", label: "End" };
    case "message":
      return { type: "message", label: "Message", message: "Hello! How can I help you?" };
    case "entity":
      return { type: "entity", label: "Entity", entityName: "", entityType: "string", prompt: "" };
    case "confirmation":
      return { type: "confirmation", label: "Confirmation", question: "Is that correct?", yesLabel: "Yes", noLabel: "No" };
    case "tool":
      return { type: "tool", label: "Tool", toolName: "", description: "" };
  }
};

interface FlowCanvasProps {
  flowId: string;
}

const FlowCanvas = ({ flowId }: FlowCanvasProps) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(null);
  const [flowName, setFlowName] = useState("");
  const [loading, setLoading] = useState(true);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const skipNextSave = useRef(true);

  // ── Load flow from backend ──
  useEffect(() => {
    const load = async () => {
      try {
        const flow = await flowsApi.get(flowId);
        setFlowName(flow.name);
        const apiNodes: Node[] = (flow.nodes as { id: string; type: string; data: Record<string, unknown>; position: { x: number; y: number } }[]).map((n) => ({
          id: n.id,
          type: "custom",
          position: n.position,
          data: n.data,
        }));
        const apiEdges: Edge[] = (flow.edges as { id: string; source: string; target: string; data?: Record<string, unknown>; sourceHandle?: string; targetHandle?: string }[]).map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
          type: "condition",
          animated: true,
          style: { stroke: "hsl(220, 15%, 40%)" },
          data: e.data || {},
        }));
        setNodes(apiNodes);
        setEdges(apiEdges);
        // Set nodeId counter past existing IDs
        const maxId = apiNodes.reduce((max, n) => {
          const num = parseInt(n.id.replace(/\D/g, ""), 10);
          return isNaN(num) ? max : Math.max(max, num);
        }, 0);
        nodeId = maxId;
      } catch (err: unknown) {
        toast.error(err instanceof Error ? err.message : "Failed to load flow");
      } finally {
        setLoading(false);
        // Allow saves after initial load settles
        setTimeout(() => { skipNextSave.current = false; }, 500);
      }
    };
    load();
  }, [flowId, setNodes, setEdges]);

  // ── Debounced auto-save ──
  const saveToBackend = useCallback(() => {
    if (skipNextSave.current) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        const backendNodes = nodes.map((n) => ({
          id: n.id,
          type: (n.data as unknown as FlowNodeData).type,
          position: n.position,
          data: n.data,
        }));
        const backendEdges = edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
          data: e.data || {},
        }));
        await flowsApi.update(flowId, { nodes: backendNodes, edges: backendEdges });
      } catch {
        // silent — avoid spamming the user
      }
    }, 1500);
  }, [flowId, nodes, edges]);

  useEffect(() => {
    saveToBackend();
  }, [nodes, edges, saveToBackend]);

  const onConnect = useCallback(
    (params: Connection) => {
      // Auto-label edges from confirmation nodes
      const sourceNode = nodes.find((n) => n.id === params.source);
      const sourceData = sourceNode?.data as unknown as FlowNodeData | undefined;
      let label: string | undefined;
      if (sourceData?.type === "confirmation") {
        if (params.sourceHandle === "yes") label = sourceData.yesLabel || "Yes";
        else if (params.sourceHandle === "no") label = sourceData.noLabel || "No";
      }
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: "condition",
            animated: true,
            style: { stroke: 'hsl(220, 15%, 40%)' },
            data: label ? { label } : {},
          },
          eds
        )
      );
    },
    [setEdges, nodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData("application/reactflow") as NodeType;
      if (!type || !reactFlowInstance || !reactFlowWrapper.current) return;

      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });

      const newNode: Node = {
        id: getNodeId(),
        type: "custom",
        position,
        data: defaultDataForType(type) as Record<string, unknown>,
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [reactFlowInstance, setNodes]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleNodeDataChange = useCallback(
    (id: string, newData: FlowNodeData) => {
      setNodes((nds) =>
        nds.map((n) => (n.id === id ? { ...n, data: newData as Record<string, unknown> } : n))
      );
      setSelectedNode((prev) => (prev && prev.id === id ? { ...prev, data: newData as Record<string, unknown> } : prev));
    },
    [setNodes]
  );

  const handleExportJSON = useCallback(async () => {
    try {
      const flow = {
        nodes: nodes.map((n) => ({
          id: n.id,
          type: (n.data as unknown as FlowNodeData).type,
          position: n.position,
          data: n.data,
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
        })),
      };
      const json = JSON.stringify(flow, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${flowName.replace(/\s+/g, "_") || "dialog-flow"}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Flow exported as JSON!");
    } catch {
      toast.error("Export failed");
    }
  }, [nodes, edges, flowName]);

  const handleClear = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    toast.info("Canvas cleared");
  }, [setNodes, setEdges]);

  const handleLoadExample = useCallback(() => {
    nodeId = 8;
    const exampleNodes: Node[] = [
      { id: "node_1", type: "custom", position: { x: 250, y: 0 }, data: { type: "start", label: "Start" } as Record<string, unknown> },
      { id: "node_2", type: "custom", position: { x: 250, y: 120 }, data: { type: "message", label: "Welcome", message: "Welcome to PizzaBot! 🍕 I can help you order a pizza." } as Record<string, unknown> },
      { id: "node_3", type: "custom", position: { x: 250, y: 270 }, data: { type: "entity", label: "Get Pizza Size", entityName: "pizzaSize", entityType: "string", prompt: "What size pizza would you like? (Small, Medium, Large)" } as Record<string, unknown> },
      { id: "node_4", type: "custom", position: { x: 250, y: 440 }, data: { type: "entity", label: "Get Toppings", entityName: "toppings", entityType: "string", prompt: "What toppings would you like?" } as Record<string, unknown> },
      { id: "node_5", type: "custom", position: { x: 250, y: 610 }, data: { type: "confirmation", label: "Confirm Order", question: "You want a {{pizzaSize}} pizza with {{toppings}}. Place order?", yesLabel: "Yes", noLabel: "No" } as Record<string, unknown> },
      { id: "node_6", type: "custom", position: { x: 50, y: 800 }, data: { type: "tool", label: "Place Order", toolName: "placeOrder", description: "Calls the order API to place the pizza order" } as Record<string, unknown> },
      { id: "node_7", type: "custom", position: { x: 450, y: 800 }, data: { type: "message", label: "Cancelled", message: "No problem! Let me know if you change your mind." } as Record<string, unknown> },
      { id: "node_8", type: "custom", position: { x: 250, y: 960 }, data: { type: "end", label: "End" } as Record<string, unknown> },
    ];
    const exampleEdges: Edge[] = [
      { id: "e1-2", source: "node_1", target: "node_2", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: {} },
      { id: "e2-3", source: "node_2", target: "node_3", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: {} },
      { id: "e3-4", source: "node_3", target: "node_4", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: {} },
      { id: "e4-5", source: "node_4", target: "node_5", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: {} },
      { id: "e5-6", source: "node_5", sourceHandle: "yes", target: "node_6", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: { label: "Yes" } },
      { id: "e5-7", source: "node_5", sourceHandle: "no", target: "node_7", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: { label: "No" } },
      { id: "e6-8", source: "node_6", target: "node_8", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: {} },
      { id: "e7-8", source: "node_7", target: "node_8", type: "condition", animated: true, style: { stroke: 'hsl(220, 15%, 40%)' }, data: {} },
    ];
    setNodes(exampleNodes);
    setEdges(exampleEdges);
    setSelectedNode(null);
    toast.success("Example pizza order flow loaded!");
  }, [setNodes, setEdges]);

  // Apply highlighting to nodes
  const displayNodes = nodes.map((n) => ({
    ...n,
    style: highlightedNodeId
      ? n.id === highlightedNodeId
        ? { ...n.style, boxShadow: "0 0 0 3px hsl(220, 70%, 55%)", borderRadius: "8px" }
        : { ...n.style, opacity: 0.4 }
      : n.style,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen w-full bg-background">
        <p className="text-sm text-muted-foreground">Loading flow...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-full">
      <FlowToolbar flowName={flowName} onExportJSON={handleExportJSON} onClear={handleClear} onTestFlow={() => setShowTestPanel(true)} onLoadExample={handleLoadExample} />
      <div className="flex flex-1 overflow-hidden">
        <NodeSidebar />
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={displayNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={(instance) => setReactFlowInstance(instance as unknown as ReactFlowInstance)}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            deleteKeyCode={["Backspace", "Delete"]}
            className="bg-canvas-bg"
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(220, 15%, 18%)" />
            <Controls />
            <MiniMap
              style={{ background: "hsl(220, 18%, 12%)" }}
              maskColor="hsl(220, 20%, 8%, 0.7)"
              nodeColor="hsl(220, 70%, 55%)"
            />
          </ReactFlow>
        </div>
        {selectedNode && !showTestPanel && (
          <NodePropertiesPanel
            node={selectedNode}
            onChange={handleNodeDataChange}
            onClose={() => setSelectedNode(null)}
          />
        )}
        {showTestPanel && (
          <ChatTestPanel
            nodes={nodes}
            edges={edges}
            onClose={() => { setShowTestPanel(false); setHighlightedNodeId(null); }}
            onHighlightNode={setHighlightedNodeId}
          />
        )}
      </div>
    </div>
  );
};

export default FlowCanvas;
