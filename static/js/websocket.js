/**
 * Flowboard Real-time WebSocket Client
 * Automatic reconnect with exponential backoff & presence management.
 */

(function () {
  'use strict';

  class RealtimeSocket {
    constructor(path, onMessage, onOpen = null) {
      this.path = path;
      this.onMessage = onMessage;
      this.onOpen = onOpen;
      this.socket = null;
      this.retryCount = 0;
      this.maxDelay = 10000;
      this.isClosedExplicitly = false;
      this.pingInterval = null;
      this.connect();
    }

    connect() {
      if (this.isClosedExplicitly) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = `${protocol}//${window.location.host}${this.path}`;

      try {
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
          this.retryCount = 0;
          if (this.onOpen) this.onOpen();

          // Heartbeat ping every 25s
          clearInterval(this.pingInterval);
          this.pingInterval = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
              this.socket.send(JSON.stringify({ action: 'ping' }));
            }
          }, 25000);
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'pong') return;
            this.onMessage(data);
          } catch (err) {
            console.error('WS Parse Error:', err);
          }
        };

        this.socket.onclose = (event) => {
          clearInterval(this.pingInterval);
          if (!this.isClosedExplicitly) {
            // Reconnect with backoff
            const delay = Math.min(1000 * Math.pow(1.8, this.retryCount), this.maxDelay);
            this.retryCount++;
            setTimeout(() => this.connect(), delay);
          }
        };

        this.socket.onerror = (err) => {
          // Socket error handled in onclose
        };
      } catch (err) {
        setTimeout(() => this.connect(), 2000);
      }
    }

    send(data) {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(data));
      }
    }

    close() {
      this.isClosedExplicitly = true;
      clearInterval(this.pingInterval);
      if (this.socket) {
        this.socket.close();
      }
    }
  }

  window.FlowboardSocket = RealtimeSocket;
})();
