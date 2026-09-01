export interface JobProgressEvent {
  event: string;
  job_id: string;
  status: string;
  progress_pct: number;
  current_stage: string;
  timestamp: string;
}

export type JobProgressCallback = (event: JobProgressEvent) => void;

export class JobWebSocketClient {
  private ws: WebSocket | null = null;
  private jobId: string;
  private onMessage: JobProgressCallback;
  private onError?: (err: Event) => void;
  private onOpen?: () => void;
  private onClose?: () => void;
  private reconnectTimeout: any = null;
  private isExplicitClose: boolean = false;

  constructor(
    jobId: string,
    onMessage: JobProgressCallback,
    options?: {
      onError?: (err: Event) => void;
      onOpen?: () => void;
      onClose?: () => void;
    }
  ) {
    this.jobId = jobId;
    this.onMessage = onMessage;
    this.onError = options?.onError;
    this.onOpen = options?.onOpen;
    this.onClose = options?.onClose;
  }

  public connect(): void {
    this.isExplicitClose = false;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/jobs/${this.jobId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        if (this.onOpen) this.onOpen();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: JobProgressEvent = JSON.parse(event.data);
          this.onMessage(data);
        } catch (e) {
          console.error("Error parsing WebSocket event:", e);
        }
      };

      this.ws.onerror = (err) => {
        if (this.onError) this.onError(err);
      };

      this.ws.onclose = () => {
        if (this.onClose) this.onClose();
        if (!this.isExplicitClose) {
          // Reconnect with backoff
          this.reconnectTimeout = setTimeout(() => {
            this.connect();
          }, 3000);
        }
      };
    } catch (e) {
      console.error("Failed to establish WebSocket connection:", e);
    }
  }

  public disconnect(): void {
    this.isExplicitClose = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
