'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import dynamic from 'next/dynamic'; // Import dynamic
import chatLoadingAnimation from '@/../public/chatloading.json';
import { cn } from "@/lib/utils";

// Dynamically import Lottie component, disable SSR
const Lottie = dynamic(() => import('lottie-react'), { ssr: false });

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
        {/* Render Lottie animation for loading message */}
        {sender === 'loading' ? (
           <div className="w-16 h-8 flex items-center justify-center"> {/* Adjust size and center */}
             {typeof window !== 'undefined' && <Lottie animationData={chatLoadingAnimation} loop={true} />}
           </div>
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
