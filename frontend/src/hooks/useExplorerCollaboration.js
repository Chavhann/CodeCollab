import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "../api/config";

function getWebSocketBaseUrl() {
  return API_BASE_URL.replace(/^http/, "ws");
}

export default function useExplorerCollaboration({
  projectId,
  onExplorerEvent,
}) {
  const socketRef = useRef(null);
  const onExplorerEventRef = useRef(onExplorerEvent);

  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [connectionError, setConnectionError] = useState("");

  useEffect(() => {
    onExplorerEventRef.current = onExplorerEvent;
  }, [onExplorerEvent]);

  useEffect(() => {
    if (!projectId) {
      setConnectionStatus("disconnected");
      setConnectionError("");
      return undefined;
    }

    const token = localStorage.getItem("codecollab_token");

    if (!token) {
      setConnectionStatus("disconnected");
      setConnectionError("Authentication token not found.");
      return undefined;
    }

    const socketUrl =
      `${getWebSocketBaseUrl()}/ws/projects/${projectId}` +
      `?token=${encodeURIComponent(token)}`;

    const socket = new WebSocket(socketUrl);

    socketRef.current = socket;
    setConnectionStatus("connecting");
    setConnectionError("");

    socket.onopen = () => {
      setConnectionStatus("connected");
      setConnectionError("");
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === "connected") {
          return;
        }

        if (message.type === "explorer") {
          onExplorerEventRef.current?.(message);
          return;
        }

        if (message.type === "error") {
          setConnectionError(message.message || "Explorer collaboration error.");
        }
      } catch {
        setConnectionError("Received an invalid Explorer collaboration message.");
      }
    };

    socket.onerror = () => {
      setConnectionStatus("error");
      setConnectionError(
        "Unable to connect to the Explorer collaboration server.",
      );
    };

    socket.onclose = () => {
      if (socketRef.current === socket) {
        socketRef.current = null;
      }

      setConnectionStatus("disconnected");
    };

    return () => {
      socket.close();

      if (socketRef.current === socket) {
        socketRef.current = null;
      }

      setConnectionStatus("disconnected");
    };
  }, [projectId]);

  const sendExplorerEvent = useCallback((event, file = null, fileId = null) => {
    const socket = socketRef.current;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }

    socket.send(
      JSON.stringify({
        type: "explorer",
        event,
        file,
        file_id: fileId,
      }),
    );

    return true;
  }, []);

  return {
    connectionStatus,
    connectionError,
    sendExplorerEvent,
  };
}
