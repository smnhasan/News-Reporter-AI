import axios from "axios"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8008"

// Axios instance
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
})

// Request interceptor (adds token if present)
apiClient.interceptors.request.use(
  (config) => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor (handles 401)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("auth_token")
    }
    return Promise.reject(error)
  }
)

// ----------------------------
// Streaming chat (SSE)
// ----------------------------
export async function sendMessageStream(
  query: string,
  onMessage: (token: string) => void
): Promise<void> {
  const url = `${API_BASE_URL}/api/chat/stream?query=${encodeURIComponent(query)}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "text/event-stream",
    },
  });

  if (!response.body) {
    throw new Error("No response body received from server");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.replace("data: ", "").replace(/\r$/, "");
          if (data === "[DONE]") {
            return;
          }
          onMessage(data);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}


// ----------------------------
// WebSocket chat
// ----------------------------
export class WebSocketChat {
  private ws: WebSocket | null = null
  private onMessage: ((message: string) => void) | null | undefined = null
  private onError: ((error: string) => void) | null | undefined = null
  private onConnect: (() => void) | null | undefined = null
  private onDisconnect: (() => void) | null | undefined = null

  connect(
    onMessage: (message: string) => void,
    onError: (error: string) => void,
    onConnect?: () => void,
    onDisconnect?: () => void
  ): void {
    this.onMessage = onMessage
    this.onError = onError
    this.onConnect = onConnect
    this.onDisconnect = onDisconnect

    try {
      const wsUrl = API_BASE_URL.replace("http://", "ws://").replace(
        "https://",
        "wss://"
      )
      this.ws = new WebSocket(`${wsUrl}/api/ws/chat`)

      this.ws.onopen = () => {
        console.log("WebSocket connected")
        this.onConnect?.()
      }

      this.ws.onmessage = (event) => {
        this.onMessage?.(event.data)
      }

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error)
        this.onError?.("WebSocket connection error")
      }

      this.ws.onclose = () => {
        console.log("WebSocket disconnected")
        this.onDisconnect?.()
      }
    } catch (error: any) {
      console.error("Error creating WebSocket:", error)
      this.onError?.(error.message || "Failed to create WebSocket connection")
    }
  }

  sendMessage(message: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message)
    } else {
      console.error("WebSocket is not connected")
      this.onError?.("WebSocket is not connected")
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// ----------------------------
// Health check
// ----------------------------
export interface HealthResponse {
  status: string
  timestamp: string
}

export const checkHealth = async (): Promise<HealthResponse> => {
  try {
    const response = await apiClient.get<HealthResponse>("/health")
    return response.data
  } catch (error) {
    console.error("Health check failed:", error)
    throw error
  }
}

// ----------------------------
// Utility
// ----------------------------
const generateSessionId = (): string => {
  return "session_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now()
}

export { apiClient, generateSessionId }
