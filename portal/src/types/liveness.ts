// types/liveness.ts
export interface LivenessProps {
  onComplete?: (result: LivenessResult) => void;
  onError?: (error: Error) => void;
}

export interface LivenessResult {
  sessionId: string;
  isLive: boolean;
  confidence?: number;
}
export interface SessionResponse {
  sessionId: string;
  message: string;
}

export interface LivenessResponse {
  sessionId: string;
  confidence: number;
  status: string;
  isLive: boolean;
  message: string;
}

export interface DocumentValidationResponse {
  validationId?: string;
  message:string
  error?:string
}