/**
 * JSON-RPC 2.0 types and helper functions
 */

// JSON-RPC 2.0 Request object
export interface JSONRPCRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: Record<string, unknown> | unknown[];
}

// JSON-RPC 2.0 Response object
export interface JSONRPCResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: unknown;
  error?: JSONRPCError;
}

// JSON-RPC 2.0 Error object
export interface JSONRPCError {
  code: number;
  message: string;
  data?: unknown;
}

// Pre-defined JSON-RPC error codes
export const JSONRPC_ERRORS = {
  PARSE_ERROR: { code: -32700, message: 'Parse error' },
  INVALID_REQUEST: { code: -32600, message: 'Invalid Request' },
  METHOD_NOT_FOUND: { code: -32601, message: 'Method not found' },
  INVALID_PARAMS: { code: -32602, message: 'Invalid params' },
  INTERNAL_ERROR: { code: -32603, message: 'Internal error' },
  SERVER_ERROR: { code: -32000, message: 'Server error' },
} as const;

// WebSocket message types
export type WSMessage = JSONRPCRequest | JSONRPCResponse | ArrayBuffer | ping | pong;

// Ping message type
export interface ping {
  type: 'ping';
}

// Pong message type
export interface pong {
  type: 'pong';
}

/**
 * Create a JSON-RPC 2.0 request object
 */
export function createRequest(
  method: string,
  params?: Record<string, unknown> | unknown[],
  id: string | number = crypto.randomUUID()
): JSONRPCRequest {
  return {
    jsonrpc: '2.0',
    id,
    method,
    ...(params !== undefined && { params }),
  };
}

/**
 * Type guard to check if a message is a JSON-RPC response
 */
export function isJSONRPCResponse(msg: unknown): msg is JSONRPCResponse {
  if (typeof msg !== 'object' || msg === null) {
    return false;
  }
  const obj = msg as Record<string, unknown>;
  return (
    obj.jsonrpc === '2.0' &&
    'id' in obj &&
    (('result' in obj && !('error' in obj)) || ('error' in obj && !('result' in obj)))
  );
}

/**
 * Type guard to check if a message is a JSON-RPC request
 */
export function isJSONRPCRequest(msg: unknown): msg is JSONRPCRequest {
  if (typeof msg !== 'object' || msg === null) {
    return false;
  }
  const obj = msg as Record<string, unknown>;
  return (
    obj.jsonrpc === '2.0' &&
    'id' in obj &&
    'method' in obj &&
    typeof obj.method === 'string'
  );
}
