import React, { createContext, useContext, useState } from 'react';

const MCPNotificationContext = createContext();

export const useMCPNotification = () => {
  const context = useContext(MCPNotificationContext);
  if (!context) {
    throw new Error('useMCPNotification must be used within an MCPNotificationProvider');
  }
  return context;
};

export const MCPNotificationProvider = ({ children }) => {
  const [activeTools, setActiveTools] = useState(new Map());
  const [hideTimers, setHideTimers] = useState(new Map());

  const showMCPTool = (toolName, description = '') => {
    const id = `${toolName}-${Date.now()}`;
    console.log('🔧 MCP Notification: Showing tool', { toolName, description, id });
    setActiveTools(prev => {
      const newMap = new Map(prev).set(id, {
        toolName,
        description,
        startTime: Date.now()
      });
      console.log('🔧 MCP Notification: Active tools after show:', newMap.size);
      return newMap;
    });
    return id;
  };

  const hideMCPTool = (id) => {
    console.log('🔧 MCP Notification: Attempting to hide tool', { id });
    
    setActiveTools(prev => {
      const tool = prev.get(id);
      if (!tool) {
        console.log('🔧 MCP Notification: Tool not found', { id });
        return prev;
      }

      const timeElapsed = Date.now() - tool.startTime;
      const minDisplayTime = 10000; // 10 seconds minimum

      if (timeElapsed < minDisplayTime) {
        const remainingTime = minDisplayTime - timeElapsed;
        console.log('🔧 MCP Notification: Delaying hide for', remainingTime, 'ms');
        
        // Set a timer to hide after minimum time
        setHideTimers(prevTimers => {
          const newTimers = new Map(prevTimers);
          const timerId = setTimeout(() => {
            console.log('🔧 MCP Notification: Timer hiding tool', { id });
            setActiveTools(current => {
              const updated = new Map(current);
              updated.delete(id);
              return updated;
            });
            setHideTimers(current => {
              const updated = new Map(current);
              updated.delete(id);
              return updated;
            });
          }, remainingTime);
          newTimers.set(id, timerId);
          return newTimers;
        });
        
        return prev; // Don't hide yet
      } else {
        // Enough time has passed, hide immediately
        console.log('🔧 MCP Notification: Hiding tool immediately', { id });
        const newMap = new Map(prev);
        newMap.delete(id);
        return newMap;
      }
    });
  };

  const hideAllTools = () => {
    // Clear all active timers
    hideTimers.forEach(timerId => clearTimeout(timerId));
    setHideTimers(new Map());
    setActiveTools(new Map());
  };

  const value = {
    activeTools,
    showMCPTool,
    hideMCPTool,
    hideAllTools
  };

  return (
    <MCPNotificationContext.Provider value={value}>
      {children}
    </MCPNotificationContext.Provider>
  );
};

export default MCPNotificationContext;