export type NodeType = 'message' | 'entity' | 'confirmation' | 'tool';

export interface MessageNodeData {
  [key: string]: unknown;
  type: 'message';
  label: string;
  message: string;
}

export interface EntityNodeData {
  [key: string]: unknown;
  type: 'entity';
  label: string;
  entityName: string;
  entityType: string;
  prompt: string;
}

export interface ConfirmationNodeData {
  [key: string]: unknown;
  type: 'confirmation';
  label: string;
  question: string;
  yesLabel: string;
  noLabel: string;
}

export interface ToolNodeData {
  [key: string]: unknown;
  type: 'tool';
  label: string;
  toolName: string;
  description: string;
}

export type FlowNodeData = MessageNodeData | EntityNodeData | ConfirmationNodeData | ToolNodeData;
