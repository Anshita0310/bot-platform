export type NodeType = 'start' | 'end' | 'message' | 'entity' | 'confirmation' | 'tool';

export interface StartNodeData {
  [key: string]: unknown;
  type: 'start';
  label: string;
}

export interface EndNodeData {
  [key: string]: unknown;
  type: 'end';
  label: string;
}

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

export type FlowNodeData = StartNodeData | EndNodeData | MessageNodeData | EntityNodeData | ConfirmationNodeData | ToolNodeData;
