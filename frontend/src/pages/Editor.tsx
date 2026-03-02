import { useParams, Navigate } from "react-router-dom";
import FlowCanvas from "@/components/flow/FlowCanvas";

const Editor = () => {
  const { flowId } = useParams<{ flowId: string }>();
  if (!flowId) return <Navigate to="/" replace />;
  return <FlowCanvas flowId={flowId} />;
};

export default Editor;
