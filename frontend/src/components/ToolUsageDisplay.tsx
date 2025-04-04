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
  run_id: string; // Add run_id
  associatedStartTitle?: string | null; // Add for end messages
}

interface ToolUsageItemProps {
  usage: ToolUsage;
}

const ToolUsageItem: React.FC<ToolUsageItemProps> = ({ usage }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const originalContentRef = React.useRef<HTMLParagraphElement>(null);
  const [isOriginalContentTruncated, setIsOriginalContentTruncated] = useState(false);

  let displayTitle: string | null = null;
  let isMapped = false; // Flag to know if we created a custom title

  if (usage.type === 'start') {
    // Logic to extract toolName, ticker, and get mapped title
    const toolNameMatch = usage.content.match(/Running tool '([^']+)'/);
    const toolName = toolNameMatch ? toolNameMatch[1] : null;
    const tickerMatch = usage.content.match(/'ticker':\s*'([^']+)'/);
    const ticker = tickerMatch ? tickerMatch[1] : 'STOCK'; // Default ticker

    if (toolName) {
      const mapper = new ToolNameMapper(ticker);
      displayTitle = mapper.getMapping(toolName) || `Running ${toolName}...`;
      isMapped = true;
    }
    // If toolName couldn't be extracted, displayTitle remains null, show original content
  } else if (usage.type === 'end') {
    // Use the associated title if available (passed down from parent based on run_id)
    if (usage.associatedStartTitle) {
      displayTitle = `${usage.associatedStartTitle} [완료]`;
      isMapped = true;
    }
    // If no associated title, displayTitle remains null, show original content
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

  // Check if the *original* content needs truncation for the "Show more" button
  useEffect(() => {
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
      {isMapped ? (
        // Display mapped title (start or completed end)
        <>
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
            {isExpanded ? 'Show less' : 'Show more'}
            {isExpanded ? <ChevronUp className="ml-1 h-3 w-3" /> : <ChevronDown className="ml-1 h-3 w-3" />}
          </Button>
          {/* Original content shown when expanded */}
          {isExpanded && (
             <p ref={originalContentRef} className="mt-1 whitespace-pre-wrap break-words text-muted-foreground">
               {usage.content}
             </p>
          )}
        </>
      ) : (
        // Original display logic (unmappable start/end, or regular end without association)
        <>
          <p
            ref={originalContentRef}
            className={`whitespace-pre-wrap break-words ${
              !isExpanded && isOriginalContentTruncated ? 'line-clamp-1' : ''
            }`}
          >
            {usage.content}
          </p>
          {isOriginalContentTruncated && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-auto p-0 text-xs text-muted-foreground hover:bg-transparent"
            >
             {isExpanded ? 'Show less' : 'Show more'}
             {isExpanded ? <ChevronUp className="ml-1 h-3 w-3" /> : <ChevronDown className="ml-1 h-3 w-3" />}
            </Button>
          )}
        </>
      )}
    </div>
  );
};


const ToolUsageDisplay: React.FC = () => {
  const [toolUsages, setToolUsages] = useState<ToolUsage[]>([]);
  const usageIdCounter = useRef(0);
  // Use useRef for synchronous access to the map within the WebSocket handler
  const startTitlesMapRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
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
          // Validate the received data structure, now including run_id
          if (messageData && typeof messageData === 'object' && messageData.type && messageData.content && messageData.timestamp && messageData.run_id) {
            const type = messageData.type === 'start' ? 'start' : 'end';
            const content = messageData.content;
            const timestamp = new Date(messageData.timestamp).toLocaleTimeString();
            const run_id = messageData.run_id;
            const id = usageIdCounter.current++;

            let newUsage: ToolUsage;
            let associatedStartTitle: string | null = null;

            if (type === 'start') {
              // Extract toolName and ticker to generate mapped title
              const toolNameMatch = content.match(/Running tool '([^']+)'/);
              const toolName = toolNameMatch ? toolNameMatch[1] : null;
              const tickerMatch = content.match(/'ticker':\s*'([^']+)'/);
              const ticker = tickerMatch ? tickerMatch[1] : 'STOCK';

              if (toolName) {
                const mapper = new ToolNameMapper(ticker);
                const mappedTitle = mapper.getMapping(toolName) || `Running ${toolName}...`;
                // Store the title directly in the ref's current map
                startTitlesMapRef.current.set(run_id, mappedTitle);
              } else {
                 // Store a fallback title if name extraction fails
                 startTitlesMapRef.current.set(run_id, `Running unknown tool...`);
              }
              newUsage = { id, type, content, timestamp, run_id }; // No associated title needed for start
            } else { // type === 'end'
              // Look up the associated start title directly from the ref's current map
              associatedStartTitle = startTitlesMapRef.current.get(run_id) || null;
              newUsage = {
                id,
                type,
                content,
                timestamp,
                run_id,
                associatedStartTitle // Pass the found title (or null)
              };
              // Optional: Clean up the map entry in the ref if desired
              // startTitlesMapRef.current.delete(run_id);
            }

            setToolUsages((prevUsages) => [...prevUsages, newUsage]);

          } else {
            console.warn('Received invalid WebSocket message format (missing fields?):', messageData);
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
