'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from "@/lib/utils";

// Simple SVG Spinner Component (Copied from page.tsx for encapsulation)
const LoadingSpinner = () => (
    <svg
        className="animate-spin h-5 w-5 text-primary"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
    >
        <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
        ></circle>
        <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
    </svg>
);

interface ChatMessageBubbleProps {
  sender: string; // 'user', agent name, 'loading', 'error', 'system'
  text: string;
}

const TRUNCATE_LENGTH = 200; // Number of characters to show initially

export function ChatMessageBubble({ sender, text }: ChatMessageBubbleProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const isAgentMessage = sender !== 'user' && sender !== 'loading' && sender !== 'error' && sender !== 'system';
  const isLongMessage = text.length > TRUNCATE_LENGTH;
  const showExpandable = isAgentMessage && isLongMessage;

  const handleToggleExpand = () => {
    if (showExpandable) {
      setIsExpanded(!isExpanded);
    }
  };

  const displayText = showExpandable && !isExpanded ? `${text.substring(0, TRUNCATE_LENGTH)}...` : text;

  return (
    <div
      className={cn(
        "flex",
        sender === 'user' ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl p-3 rounded-lg shadow",
          sender === 'user' ? "bg-primary text-primary-foreground"
          : sender === 'loading' ? "bg-muted p-2" // Style for loading bubble
          : sender === 'error' || sender === 'system' ? "bg-destructive text-destructive-foreground"
          : "bg-muted", // Default agent style
          showExpandable ? "cursor-pointer hover:shadow-md transition-shadow" : "" // Add cursor pointer for expandable messages
        )}
        onClick={handleToggleExpand}
      >
        {/* Render Spinner for loading message */}
        {sender === 'loading' ? (
          <LoadingSpinner />
        ) : sender !== 'user' ? (
          <>
            {/* Show sender name only for agent/error/system messages */}
            {(sender !== 'error' && sender !== 'system') && (
                <p className="text-xs font-semibold mb-1 capitalize">{sender}</p>
            )}
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {displayText}
              </ReactMarkdown>
            </div>
            {showExpandable && !isExpanded && (
              <div className="text-right text-xs text-muted-foreground mt-1">Click to expand</div>
            )}
          </>
        ) : (
          <p className="whitespace-pre-wrap">{text}</p> // User message
        )}
      </div>
    </div>
  );
}
