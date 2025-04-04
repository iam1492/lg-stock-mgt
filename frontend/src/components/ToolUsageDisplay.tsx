'use client';

import React, { useState, useEffect, useRef } from 'react'; // Added useRef
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface ToolUsage {
  id: number;
  type: 'start' | 'end';
  content: string;
  timestamp: string;
}

interface ToolUsageItemProps {
  usage: ToolUsage;
}

const ToolUsageItem: React.FC<ToolUsageItemProps> = ({ usage }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isTruncated, setIsTruncated] = useState(false);
  const contentRef = React.useRef<HTMLParagraphElement>(null);

  // Remove the prefix, as it's included in the content from backend now
  const displayContent = usage.content;

  useEffect(() => {
    if (contentRef.current) {
      // Check if the content is taller than one line height (approx 24px for typical line-height)
      setIsTruncated(contentRef.current.scrollHeight > 24);
    }
  }, [displayContent]);

  return (
    <div className="mb-2 text-sm">
      <p
        ref={contentRef}
        className={`whitespace-pre-wrap break-words ${
          !isExpanded && isTruncated ? 'line-clamp-1' : ''
        }`}
      >
        {displayContent}
      </p>
      {isTruncated && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="h-auto p-0 text-xs text-muted-foreground hover:bg-transparent"
        >
          {isExpanded ? (
            <>
              Show less <ChevronUp className="ml-1 h-3 w-3" />
            </>
          ) : (
            <>
              Show more <ChevronDown className="ml-1 h-3 w-3" />
            </>
          )}
        </Button>
      )}
      {/* Removed timestamp paragraph */}
    </div>
  );
};


const ToolUsageDisplay: React.FC = () => {
  const [toolUsages, setToolUsages] = useState<ToolUsage[]>([]);
  const usageIdCounter = useRef(0); // Ref to ensure unique IDs for keys

  useEffect(() => {
    // Ensure WebSocket runs only on the client side
    if (typeof window === 'undefined') {
      return;
    }

    const wsUrl = 'ws://localhost:8080/ws/tool_usage'; // Ensure port matches backend
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const connectWebSocket = () => {
      console.log('Attempting to connect WebSocket...');
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        // Clear any reconnect timeout upon successful connection
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const messageData = JSON.parse(event.data);
          // Validate the received data structure
          if (messageData && typeof messageData === 'object' && messageData.type && messageData.content && messageData.timestamp) {
            const newUsage: ToolUsage = {
              id: usageIdCounter.current++, // Use counter for unique ID
              type: messageData.type === 'start' ? 'start' : 'end',
              content: messageData.content,
              // Format timestamp for better readability
              timestamp: new Date(messageData.timestamp).toLocaleTimeString(),
            };
            setToolUsages((prevUsages) => [...prevUsages, newUsage]);
          } else {
            console.warn('Received invalid WebSocket message format:', messageData);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message or update state:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Optionally close the connection explicitly on error before attempting reconnect
        ws?.close();
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: Code=${event.code}, Reason=${event.reason}`);
        // Attempt to reconnect after a delay, unless it was a clean close (e.g., code 1000)
        if (event.code !== 1000 && !reconnectTimeout) {
          console.log('Attempting to reconnect WebSocket in 5 seconds...');
          reconnectTimeout = setTimeout(connectWebSocket, 5000);
        }
      };
    };

    connectWebSocket(); // Initial connection attempt

    // Cleanup function: close WebSocket and clear timeout on component unmount
    return () => {
      console.log('Cleaning up WebSocket connection.');
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.onclose = null; // Prevent triggering reconnect logic during cleanup
        ws.close(1000, "Component unmounting"); // Clean close
      }
    };
  }, []); // Empty dependency array ensures this runs only once on mount

  return (
    <Card className="h-full shadow-md rounded-lg overflow-hidden flex flex-col">
      <CardHeader className="p-3 border-b flex-shrink-0"> {/* Reduced padding */}
        <CardTitle className="text-base font-semibold">Tool Usages</CardTitle> {/* Reduced title size */}
      </CardHeader>
      {/* Make CardContent grow and scroll, reduce padding and text size */}
      <CardContent className="p-3 flex-grow overflow-y-auto text-xs"> {/* Reduced padding and base text size */}
        {toolUsages.length === 0 ? (
          <p className="text-xs text-muted-foreground">Waiting for tool usages...</p> /* Matched text size */
        ) : (
          toolUsages.map((usage) => (
            <ToolUsageItem key={usage.id} usage={usage} />
          ))
        )}
      </CardContent>
    </Card>
  );
}; 

export default ToolUsageDisplay;
