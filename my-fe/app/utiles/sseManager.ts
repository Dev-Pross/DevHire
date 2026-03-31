export type SSEStatus = "connected" | "reconnecting" | "closed";

interface SSEManagerOptions {
  url: string;
  withCredentials?: boolean;
  staleThresholdMs?: number;
  healthCheckIntervalMs?: number;
  reconnectBaseDelayMs?: number;
  reconnectMaxDelayMs?: number;
  maxReconnectAttempts?: number;
}

export class SSEManager {
  private es: EventSource | null = null;
  private readonly options: Required<SSEManagerOptions>;
  private readonly visibilityHandler: () => void;

  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private healthTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectAttempts = 0;
  private destroyed = false;
  private lastEventAt = Date.now();

  onEvent: (payload: any) => void = () => {};
  onStatusChange: (status: SSEStatus, reason?: string) => void = () => {};
  onTerminalError: (message: string) => void = () => {};

  constructor(options: SSEManagerOptions) {
    this.options = {
      withCredentials: true,
      staleThresholdMs: 90_000,
      healthCheckIntervalMs: 15_000,
      reconnectBaseDelayMs: 1_500,
      reconnectMaxDelayMs: 12_000,
      maxReconnectAttempts: 0,
      ...options,
    };

    this.visibilityHandler = () => {
      if (document.visibilityState !== "visible" || this.destroyed) {
        return;
      }

      const isOpen = this.es?.readyState === EventSource.OPEN;
      const isStale = Date.now() - this.lastEventAt > this.options.staleThresholdMs;
      if (!isOpen || isStale) {
        this.forceReconnect("tab-visible-reconnect");
      }
    };

    document.addEventListener("visibilitychange", this.visibilityHandler);
    this.connect();
  }

  private connect(): void {
    if (this.destroyed) {
      return;
    }

    this.clearReconnectTimer();
    this.closeEventSource();

    this.onStatusChange("reconnecting", "connecting");

    this.es = new EventSource(this.options.url, {
      withCredentials: this.options.withCredentials,
    });

    this.es.onopen = () => {
      this.reconnectAttempts = 0;
      this.lastEventAt = Date.now();
      this.onStatusChange("connected");
      this.startHealthCheck();
    };

    this.es.onmessage = (event: MessageEvent) => {
      this.lastEventAt = Date.now();

      if (!event.data) {
        return;
      }

      try {
        const parsed = JSON.parse(event.data);
        this.onEvent(parsed);
      } catch {
        this.onEvent({ message: event.data, status: "processing" });
      }
    };

    this.es.onerror = () => {
      this.scheduleReconnect("eventsource-error");
    };
  }

  private startHealthCheck(): void {
    this.clearHealthTimer();

    this.healthTimer = setInterval(() => {
      if (this.destroyed) {
        return;
      }

      const staleFor = Date.now() - this.lastEventAt;
      if (staleFor > this.options.staleThresholdMs) {
        this.scheduleReconnect("stale-stream");
      }
    }, this.options.healthCheckIntervalMs);
  }

  private scheduleReconnect(reason: string): void {
    if (this.destroyed) {
      return;
    }

    this.onStatusChange("reconnecting", reason);

    this.closeEventSource();
    this.clearHealthTimer();

    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts += 1;
    const maxAttempts = this.options.maxReconnectAttempts;
    if (maxAttempts > 0 && this.reconnectAttempts > maxAttempts) {
      this.onTerminalError("Unable to reconnect to stream.");
      this.destroy();
      return;
    }

    const attempt = Math.max(this.reconnectAttempts - 1, 0);
    const delay = Math.min(
      this.options.reconnectBaseDelayMs * Math.pow(2, attempt),
      this.options.reconnectMaxDelayMs,
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private forceReconnect(reason: string): void {
    if (this.destroyed) {
      return;
    }

    this.reconnectAttempts = 0;
    this.clearReconnectTimer();
    this.closeEventSource();
    this.clearHealthTimer();
    this.onStatusChange("reconnecting", reason);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 150);
  }

  private closeEventSource(): void {
    if (this.es) {
      this.es.close();
      this.es = null;
    }
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private clearHealthTimer(): void {
    if (this.healthTimer) {
      clearInterval(this.healthTimer);
      this.healthTimer = null;
    }
  }

  destroy(): void {
    if (this.destroyed) {
      return;
    }

    this.destroyed = true;
    this.clearReconnectTimer();
    this.clearHealthTimer();
    this.closeEventSource();
    document.removeEventListener("visibilitychange", this.visibilityHandler);
    this.onStatusChange("closed");
  }
}
