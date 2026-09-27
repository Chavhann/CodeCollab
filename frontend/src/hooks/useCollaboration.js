import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "../api/config";

function createClientId() {
  const existing = sessionStorage.getItem("codecollab_client_id");

  if (existing) {
    return existing;
  }

  const id =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  sessionStorage.setItem("codecollab_client_id", id);

  return id;
}

function createOperationId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function getWebSocketBaseUrl() {
  return API_BASE_URL.replace(/^http/, "ws");
}

function getTextChange(previousValue, nextValue) {
  let start = 0;

  while (
    start < previousValue.length &&
    start < nextValue.length &&
    previousValue[start] === nextValue[start]
  ) {
    start += 1;
  }

  let previousEnd = previousValue.length;
  let nextEnd = nextValue.length;

  while (
    previousEnd > start &&
    nextEnd > start &&
    previousValue[previousEnd - 1] === nextValue[nextEnd - 1]
  ) {
    previousEnd -= 1;
    nextEnd -= 1;
  }

  const deletedText = previousValue.slice(start, previousEnd);
  const insertedText = nextValue.slice(start, nextEnd);

  return {
    position: start,
    deletedText,
    insertedText,
  };
}

export default function useCollaboration({
  projectId,
  fileId,
  initialContent = "",
  onRemoteContent,
}) {
  const socketRef = useRef(null);
  const contentRef = useRef(initialContent);
  const suppressChangesRef = useRef(false);
  const onRemoteContentRef = useRef(onRemoteContent);
  const clientIdRef = useRef(null);

  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [connectionError, setConnectionError] = useState("");
  const [presence, setPresence] = useState([]);

  if (!clientIdRef.current) {
    clientIdRef.current = createClientId();
  }

  useEffect(() => {
    onRemoteContentRef.current = onRemoteContent;
  }, [onRemoteContent]);

  useEffect(() => {
    contentRef.current = initialContent;
  }, [initialContent, fileId]);

  useEffect(() => {
    if (!projectId || !fileId) {
      setConnectionStatus("disconnected");
      setPresence([]);
      return undefined;
    }

    const token = localStorage.getItem("codecollab_token");

    if (!token) {
      setConnectionStatus("disconnected");
      setConnectionError("Authentication token not found.");
      return undefined;
    }

    const socketUrl =
      `${getWebSocketBaseUrl()}/ws/projects/${projectId}/files/${fileId}` +
      `?token=${encodeURIComponent(token)}`;

    const socket = new WebSocket(socketUrl);

    socketRef.current = socket;
    setConnectionStatus("connecting");
    setConnectionError("");
    setPresence([]);

    socket.onopen = () => {
      setConnectionStatus("connected");
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === "connected") {
          suppressChangesRef.current = true;
          contentRef.current = message.content || "";

          onRemoteContentRef.current?.(message.content || "");

          window.setTimeout(() => {
            suppressChangesRef.current = false;
          }, 0);

          return;
        }

        if (message.type === "crdt") {
          suppressChangesRef.current = true;
          contentRef.current = message.content || "";

          onRemoteContentRef.current?.(message.content || "");

          window.setTimeout(() => {
            suppressChangesRef.current = false;
          }, 0);

          return;
        }

        if (message.type === "presence") {
          setPresence((current) => {
            if (message.event === "joined") {
              const existing = current.filter(
                (item) => item.user_id !== message.user_id,
              );

              return [
                ...existing,
                {
                  user_id: message.user_id,
                  username: message.username,
                  status: "online",
                },
              ];
            }

            if (message.event === "left") {
              return current.filter(
                (item) => item.user_id !== message.user_id,
              );
            }

            if (message.event === "status") {
              const existing = current.filter(
                (item) => item.user_id !== message.user_id,
              );

              return [
                ...existing,
                {
                  user_id: message.user_id,
                  username: message.username,
                  status: message.status,
                  cursor: message.cursor,
                  selection_start: message.selection_start,
                  selection_end: message.selection_end,
                  metadata: message.metadata,
                },
              ];
            }

            return current;
          });

          return;
        }

        if (message.type === "cursor") {
          setPresence((current) => {
            const existing = current.filter(
              (item) => item.user_id !== message.user_id,
            );

            const previous = current.find(
              (item) => item.user_id === message.user_id,
            );

            return [
              ...existing,
              {
                user_id: message.user_id,
                username: message.username,
                status: previous?.status || "online",
                cursor: message.cursor,
                selection_start: message.selection_start,
                selection_end: message.selection_end,
                metadata: previous?.metadata || {},
              },
            ];
          });

          return;
        }
        if (message.type === "error") {
          setConnectionError(message.message || "Collaboration error.");
        }
      } catch {
        setConnectionError("Received an invalid collaboration message.");
      }
    };

    socket.onerror = () => {
      setConnectionStatus("error");
      setConnectionError("Unable to connect to the collaboration server.");
    };

    socket.onclose = () => {
      if (socketRef.current === socket) {
        socketRef.current = null;
      }

      setConnectionStatus("disconnected");
    };

    return () => {
      socket.close();
      setPresence([]);
      setConnectionStatus("disconnected");
    };
  }, [projectId, fileId]);

  const handleCursorChange = useCallback(
    (cursorData) => {
      const socket = socketRef.current;

      if (!socket || socket.readyState !== WebSocket.OPEN) {
        return;
      }

      socket.send(
        JSON.stringify({
          type: "cursor",
          cursor: {
            line: cursorData.line,
            column: cursorData.column,
          },
          selection_start: cursorData.selectionStart || null,
          selection_end: cursorData.selectionEnd || null,
        }),
      );
    },
    [],
  );
  const handleLocalChange = useCallback(
    (nextContent) => {
      const previousContent = contentRef.current;

      if (suppressChangesRef.current) {
        contentRef.current = nextContent;
        return;
      }

      if (nextContent === previousContent) {
        return;
      }

      contentRef.current = nextContent;

      const change = getTextChange(previousContent, nextContent);
      const socket = socketRef.current;

      if (!socket || socket.readyState !== WebSocket.OPEN) {
        return;
      }

      if (change.deletedText.length > 0) {
        socket.send(
          JSON.stringify({
            type: "crdt",
            operation: {
              type: "delete",
              position: change.position,
              text: "",
              length: change.deletedText.length,
              operation_id: createOperationId(),
              client_id: clientIdRef.current,
              revision: 0,
            },
          }),
        );
      }

      if (change.insertedText.length > 0) {
        socket.send(
          JSON.stringify({
            type: "crdt",
            operation: {
              type: "insert",
              position: change.position,
              text: change.insertedText,
              length: 0,
              operation_id: createOperationId(),
              client_id: clientIdRef.current,
              revision: 0,
            },
          }),
        );
      }
    },
    [],
  );

  return {
    connectionStatus,
    connectionError,
    presence,
    handleLocalChange,
    handleCursorChange,
  };
}



