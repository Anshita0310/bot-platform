import { useState, useCallback, useRef, useEffect } from "react";
import { X, Play, RotateCcw, Send, Bot, User } from "lucide-react";
import type { Node, Edge } from "@xyflow/react";
import type { FlowNodeData } from "@/types/flow";

interface Props {
  nodes: Node[];
  edges: Edge[];
  onClose: () => void;
  onHighlightNode: (nodeId: string | null) => void;
}

interface ChatMessage {
  role: "bot" | "user";
  text: string;
}

const ChatTestPanel = ({ nodes, edges, onClose, onHighlightNode }: Props) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const [waitingForInput, setWaitingForInput] = useState(false);
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const findStartNode = useCallback((): Node | null => {
    const targetIds = new Set(edges.map((e) => e.target));
    const roots = nodes.filter((n) => !targetIds.has(n.id));
    return roots[0] || nodes[0] || null;
  }, [nodes, edges]);

  const getNextNodes = useCallback(
    (nodeId: string, handleId?: string): Node[] => {
      const outEdges = edges.filter(
        (e) => e.source === nodeId && (handleId ? e.sourceHandle === handleId : !e.sourceHandle || e.sourceHandle === null)
      );
      return outEdges
        .map((e) => nodes.find((n) => n.id === e.target))
        .filter(Boolean) as Node[];
    },
    [nodes, edges]
  );

  const processNode = useCallback(
    (node: Node) => {
      const data = node.data as unknown as FlowNodeData;
      setCurrentNodeId(node.id);
      onHighlightNode(node.id);

      switch (data.type) {
        case "message":
          setMessages((prev) => [...prev, { role: "bot", text: data.message || "(empty message)" }]);
          // Auto-advance after a short delay
          setTimeout(() => {
            const nextNodes = getNextNodes(node.id);
            if (nextNodes.length > 0) {
              processNode(nextNodes[0]);
            } else {
              setFinished(true);
              setMessages((prev) => [...prev, { role: "bot", text: "✅ Flow complete!" }]);
              onHighlightNode(null);
            }
          }, 600);
          break;

        case "entity":
          setMessages((prev) => [
            ...prev,
            { role: "bot", text: data.prompt || `Please provide your ${data.entityName || "input"}:` },
          ]);
          setWaitingForInput(true);
          break;

        case "confirmation":
          setMessages((prev) => [
            ...prev,
            { role: "bot", text: data.question || "Please confirm:" },
          ]);
          setWaitingForInput(true);
          break;

        case "tool":
          setMessages((prev) => [
            ...prev,
            { role: "bot", text: `⚙️ Running tool: ${data.toolName || "unnamed"}` },
          ]);
          setTimeout(() => {
            setMessages((prev) => [
              ...prev,
              { role: "bot", text: `✓ Tool "${data.toolName || "unnamed"}" executed successfully` },
            ]);
            const nextNodes = getNextNodes(node.id);
            if (nextNodes.length > 0) {
              setTimeout(() => processNode(nextNodes[0]), 400);
            } else {
              setFinished(true);
              setMessages((prev) => [...prev, { role: "bot", text: "✅ Flow complete!" }]);
              onHighlightNode(null);
            }
          }, 800);
          break;
      }
    },
    [getNextNodes, onHighlightNode]
  );

  const handleStart = useCallback(() => {
    const startNode = findStartNode();
    if (!startNode) return;
    setStarted(true);
    setFinished(false);
    setMessages([]);
    processNode(startNode);
  }, [findStartNode, processNode]);

  const handleReset = useCallback(() => {
    setStarted(false);
    setFinished(false);
    setMessages([]);
    setInput("");
    setCurrentNodeId(null);
    setWaitingForInput(false);
    onHighlightNode(null);
  }, [onHighlightNode]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !currentNodeId) return;
    const node = nodes.find((n) => n.id === currentNodeId);
    if (!node) return;
    const data = node.data as unknown as FlowNodeData;

    setMessages((prev) => [...prev, { role: "user", text: input.trim() }]);
    setWaitingForInput(false);

    if (data.type === "confirmation") {
      const isYes = /^(yes|y|yeah|yep|sure|ok|confirm|1)$/i.test(input.trim());
      const handleId = isYes ? "yes" : "no";

      // Try specific handle first, then fallback to default
      let nextNodes = getNextNodes(currentNodeId, handleId);
      if (nextNodes.length === 0) {
        nextNodes = getNextNodes(currentNodeId);
      }

      setInput("");
      if (nextNodes.length > 0) {
        setTimeout(() => processNode(nextNodes[0]), 400);
      } else {
        setFinished(true);
        setMessages((prev) => [...prev, { role: "bot", text: "✅ Flow complete!" }]);
        onHighlightNode(null);
      }
    } else {
      // Entity or other node that accepts input
      setInput("");
      const nextNodes = getNextNodes(currentNodeId);
      if (nextNodes.length > 0) {
        setTimeout(() => processNode(nextNodes[0]), 400);
      } else {
        setFinished(true);
        setMessages((prev) => [...prev, { role: "bot", text: "✅ Flow complete!" }]);
        onHighlightNode(null);
      }
    }
  }, [input, currentNodeId, nodes, getNextNodes, processNode, onHighlightNode]);

  return (
    <aside className="w-80 bg-sidebar border-l border-border flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Test Assistant</h3>
        </div>
        <div className="flex items-center gap-1">
          {started && (
            <button
              onClick={handleReset}
              className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-accent transition-colors"
              title="Reset"
            >
              <RotateCcw size={14} />
            </button>
          )}
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-accent transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {!started && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
            <div className="bg-primary/10 p-3 rounded-full">
              <Play size={24} className="text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Test your dialog flow</p>
              <p className="text-xs text-muted-foreground mt-1">
                Simulate a conversation through your flow to verify it works correctly.
              </p>
            </div>
            <button
              onClick={handleStart}
              disabled={nodes.length === 0}
              className="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              Start Test
            </button>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "bot" && (
              <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot size={12} className="text-primary" />
              </div>
            )}
            <div
              className={`max-w-[85%] px-3 py-2 rounded-lg text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground rounded-br-sm"
                  : "bg-muted text-foreground rounded-bl-sm"
              }`}
            >
              {msg.text}
            </div>
            {msg.role === "user" && (
              <div className="w-6 h-6 rounded-full bg-accent flex items-center justify-center flex-shrink-0 mt-0.5">
                <User size={12} className="text-muted-foreground" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input area */}
      {started && !finished && (
        <div className="p-3 border-t border-border">
          {waitingForInput ? (
            <>
              {/* Show quick Yes/No buttons for confirmation nodes */}
              {currentNodeId &&
                (nodes.find((n) => n.id === currentNodeId)?.data as unknown as FlowNodeData)?.type === "confirmation" && (
                  <div className="flex gap-2 mb-2">
                    <button
                      onClick={() => {
                        setInput("Yes");
                        setTimeout(() => {
                          const fakeInput = "Yes";
                          setMessages((prev) => [...prev, { role: "user", text: fakeInput }]);
                          setWaitingForInput(false);
                          let nextNodes = getNextNodes(currentNodeId!, "yes");
                          if (nextNodes.length === 0) nextNodes = getNextNodes(currentNodeId!);
                          setInput("");
                          if (nextNodes.length > 0) {
                            setTimeout(() => processNode(nextNodes[0]), 400);
                          } else {
                            setFinished(true);
                            setMessages((prev) => [...prev, { role: "bot", text: "✅ Flow complete!" }]);
                            onHighlightNode(null);
                          }
                        }, 100);
                      }}
                      className="flex-1 py-1.5 bg-node-entity/20 text-node-entity border border-node-entity/30 rounded-md text-xs font-medium hover:bg-node-entity/30 transition-colors"
                    >
                      {(nodes.find((n) => n.id === currentNodeId)?.data as unknown as FlowNodeData & { yesLabel?: string })?.yesLabel || "Yes"}
                    </button>
                    <button
                      onClick={() => {
                        setInput("No");
                        setTimeout(() => {
                          const fakeInput = "No";
                          setMessages((prev) => [...prev, { role: "user", text: fakeInput }]);
                          setWaitingForInput(false);
                          let nextNodes = getNextNodes(currentNodeId!, "no");
                          if (nextNodes.length === 0) nextNodes = getNextNodes(currentNodeId!);
                          setInput("");
                          if (nextNodes.length > 0) {
                            setTimeout(() => processNode(nextNodes[0]), 400);
                          } else {
                            setFinished(true);
                            setMessages((prev) => [...prev, { role: "bot", text: "✅ Flow complete!" }]);
                            onHighlightNode(null);
                          }
                        }, 100);
                      }}
                      className="flex-1 py-1.5 bg-destructive/20 text-destructive border border-destructive/30 rounded-md text-xs font-medium hover:bg-destructive/30 transition-colors"
                    >
                      {(nodes.find((n) => n.id === currentNodeId)?.data as unknown as FlowNodeData & { noLabel?: string })?.noLabel || "No"}
                    </button>
                  </div>
                )}
              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Type your response..."
                  className="flex-1 bg-muted border border-border rounded-md px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  autoFocus
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="p-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  <Send size={14} />
                </button>
              </div>
            </>
          ) : (
            <p className="text-xs text-muted-foreground text-center animate-pulse">Processing...</p>
          )}
        </div>
      )}

      {finished && (
        <div className="p-3 border-t border-border">
          <button
            onClick={handleReset}
            className="w-full py-2 bg-accent text-foreground rounded-md text-xs font-medium hover:bg-accent/80 transition-colors"
          >
            Run Again
          </button>
        </div>
      )}
    </aside>
  );
};

export default ChatTestPanel;
