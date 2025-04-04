'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { ToolNameMapper } from '../app/toolname_map'; // Import ToolNameMapper

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
  const originalContentRef = React.useRef<HTMLParagraphElement>(null); // Ref for original content height check
  const [isOriginalContentTruncated, setIsOriginalContentTruncated] = useState(false);

  let displayTitle: string | null = null;
  let toolName: string | null = null;
  let ticker: string | null = null;

  // Process only 'start' messages for mapping
  if (usage.type === 'start') {
    // Extract tool name using regex
    const toolNameMatch = usage.content.match(/Running tool '([^']+)'/);
    toolName = toolNameMatch ? toolNameMatch[1] : null;

    // Extract ticker using regex (simple case)
    const tickerMatch = usage.content.match(/'ticker':\s*'([^']+)'/);
    // Use extracted ticker or a default placeholder if not found
    ticker = tickerMatch ? tickerMatch[1] : 'STOCK';

    if (toolName && ticker) {
      const mapper = new ToolNameMapper(ticker);
      // Get mapped name or create a fallback
      displayTitle = mapper.getMapping(toolName) || `Running ${toolName}...`;
    } else if (toolName) {
        // Fallback if ticker extraction failed but tool name exists
        displayTitle = `Running ${toolName}...`;
    }
  }

  // Check if the *original* content needs truncation for the "Show more" button
  // This check is relevant for both mapped ('start') and unmapped ('end') messages
  useEffect(() => {
    // We need a slight delay for the ref to be populated correctly, especially when conditionally rendered
    const timer = setTimeout(() => {
        if (originalContentRef.current) {
            // Check if the original content is taller than one line height (approx 24px)
            setIsOriginalContentTruncated(originalContentRef.current.scrollHeight > 24);
        }
    }, 0);
    return () => clearTimeout(timer); // Cleanup timer
  }, [usage.content, isExpanded]); // Rerun when content changes or expansion state changes

  return (
    <div className="mb-2 text-sm">
      {displayTitle ? (
        // Mapped display for 'start' messages
        <>
          {/* Display the mapped title */}
          <p className="whitespace-pre-wrap break-words font-medium">
            {displayTitle}
          </p>
          {/* Button to toggle original content */}
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
          {/* Original content shown when expanded */}
          {isExpanded && (
             <p ref={originalContentRef} className="mt-1 whitespace-pre-wrap break-words text-muted-foreground">
               {usage.content}
             </p>
          )}
        </>
      ) : (
        // Original display logic for 'end' messages or if mapping failed
        <>
          <p
            ref={originalContentRef} // Use ref here too
            className={`whitespace-pre-wrap break-words ${
              !isExpanded && isOriginalContentTruncated ? 'line-clamp-1' : ''
            }`}
          >
            {usage.content}
          </p>
          {/* Show button only if content is actually truncated */}
          {isOriginalContentTruncated && (
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
        </>
      )}
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
