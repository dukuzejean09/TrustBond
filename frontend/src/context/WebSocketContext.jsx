import React, { createContext, useContext, useEffect, useState, useRef } from "react";
import { useAuth } from "./AuthContext";

const WebSocketContext = createContext({ lastMessage: null, refreshKey: 0 });

export const WebSocketProvider = ({ children }) => {
  const { user } = useAuth();
  const [lastMessage, setLastMessage] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  useEffect(() => {
    // Only establish a connection if the user is authenticated
    if (!user) return;

    let isComponentMounted = true;

    const connect = () => {
      if (!isComponentMounted) return;

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      
      // In development, the Vite proxy might run on 5173, but backend is exactly 8000.
      // Usually, we route WebSocket through Vite's proxy, or use direct API port.
      const host = window.location.hostname === "localhost" 
        ? "localhost:8000" 
        : window.location.host;
        
      const wsUrl = `${protocol}//${host}/api/v1/ws`;

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log("Real-time WebSocket connected.");
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
          reconnectTimeout.current = null;
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "refresh_data") {
            setLastMessage(data);
            setRefreshKey((prev) => prev + 1);
          }
        } catch (e) {
          console.error("Failed to parse WS message", e);
        }
      };

      ws.current.onclose = () => {
        console.log("WebSocket disconnected. Attempting to reconnect in 3s...");
        if (isComponentMounted) {
          reconnectTimeout.current = setTimeout(connect, 3000);
        }
      };
      
      ws.current.onerror = (error) => {
        console.error("WebSocket connection error:", error);
        ws.current.close();
      };
    };

    connect();

    return () => {
      isComponentMounted = false;
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        // Clear hooks so they don't fire when we deliberately close it
        ws.current.onclose = null;
        ws.current.onerror = null;
        ws.current.close();
      }
    };
  }, [user]);

  return (
    <WebSocketContext.Provider value={{ lastMessage, refreshKey }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useRealtime = () => useContext(WebSocketContext) || { refreshKey: 0 };
