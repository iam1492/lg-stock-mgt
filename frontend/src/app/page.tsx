'use client';

import React, { useState, useEffect, useRef, FormEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ChatMessageBubble } from "@/components/ChatMessageBubble"; // Import the new component
import { cn } from "@/lib/utils";

// Define the structure for chat messages
interface Message {
  id: number;
  sender: string; // 'user', agent name, 'loading', 'error', 'system'
  text: string;
}

// Define the structure for incoming stream data
interface StreamData {
  content?: string;
  error?: string;
}

// LoadingSpinner is now inside ChatMessageBubble.tsx

export default function Home() {
  const [company, setCompany] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isFetching, setIsFetching] = useState<boolean>(false); // Use isFetching to track background process
  const [requestNonce, setRequestNonce] = useState<number>(0);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      console.log("Fetch aborted");
    }
    setIsFetching(false); // Ensure fetching state is reset
    // Remove loading message if stop is called while loading
    setMessages(prev => prev.filter(msg => msg.sender !== 'loading'));
  };

  // Handle form submission
  const handleSubmit = (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!company) return;
    if (isFetching) {
        stopStreaming(); // Stop current stream if already fetching
    }

    const initialUserPrompt = `Analyze ${company} stock.`;
    const newUserMessage: Message = {
      id: Date.now(),
      sender: 'user',
      text: initialUserPrompt,
    };
    const loadingMessage: Message = {
        id: Date.now() + 1, // Ensure unique ID
        sender: 'loading',
        text: '...' // Placeholder text, won't be shown
    };
    // Reset messages and add user prompt + loading indicator
    setMessages([newUserMessage, loadingMessage]);

    setRequestNonce(prev => prev + 1); // Trigger the useEffect
  };

  // useEffect to handle the actual fetch and streaming logic
  useEffect(() => {
    if (requestNonce === 0) return; // Don't run on initial mount

    setIsFetching(true); // Mark as fetching
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const performFetch = async () => {
        let loadingMessageRemoved = false; // Flag to ensure loading message is removed only once
        try {
            const response = await fetch(`http://localhost:8080/stream_endpoint`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ company, user_input: null }),
                signal: controller.signal,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }
            if (!response.body) {
                throw new Error('Response body is null');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) {
                    console.log("Stream finished.");
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                let eventBoundaryIndex;
                while ((eventBoundaryIndex = buffer.indexOf('\n\n')) >= 0) {
                    const eventChunk = buffer.slice(0, eventBoundaryIndex);
                    buffer = buffer.slice(eventBoundaryIndex + 2);
                    const lines = eventChunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const jsonString = line.substring(6).trim();
                            if (jsonString) {
                                try {
                                    const data: StreamData = JSON.parse(jsonString);

                                    // Remove loading message on first valid data received
                                    if (!loadingMessageRemoved) {
                                        setMessages(prev => prev.filter(msg => msg.sender !== 'loading'));
                                        loadingMessageRemoved = true;
                                    }

                                    if (data.error) {
                                        console.error("Stream error:", data.error);
                                        setMessages((prev) => [...prev, { id: Date.now(), sender: 'error', text: `Stream Error: ${data.error}` }]);
                                    } else if (data.content) {
                                        const contentString = data.content;
                                        const separatorIndex = contentString.indexOf(': ');
                                        let agentName = 'agent';
                                        let messageText = contentString;

                                        if (separatorIndex !== -1) {
                                            agentName = contentString.substring(0, separatorIndex);
                                            messageText = contentString.substring(separatorIndex + 2);
                                        }
                                        setMessages((prev) => [...prev, { id: Date.now(), sender: agentName, text: messageText }]);
                                    }
                                } catch (parseError) {
                                    console.warn('Failed to parse JSON chunk:', jsonString, parseError);
                                    // Remove loading message even if parse fails but data received
                                     if (!loadingMessageRemoved) {
                                        setMessages(prev => prev.filter(msg => msg.sender !== 'loading'));
                                        loadingMessageRemoved = true;
                                    }
                                    setMessages((prev) => [...prev, { id: Date.now(), sender: 'system', text: `Received raw data: ${jsonString}` }]);
                                }
                            }
                        }
                    }
                }
            }
            if (buffer.trim().startsWith('data: ')) {
                const jsonString = buffer.substring(6).trim();
                 // Remove loading message if stream ends with partial data
                 if (!loadingMessageRemoved) {
                    setMessages(prev => prev.filter(msg => msg.sender !== 'loading'));
                    loadingMessageRemoved = true;
                }
                // ... (parsing logic if needed) ...
            }

        } catch (error: any) {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted by user or new request.');
            } else {
                console.error('Error fetching or processing stream:', error);
                 // Remove loading message on error
                setMessages(prev => prev.filter(msg => msg.sender !== 'loading'));
                setMessages((prev) => [...prev, { id: Date.now(), sender: 'error', text: `Error: ${error.message}` }]);
            }
        } finally {
             // Ensure loading message is removed if stream finishes/errors before any data arrived
            if (!loadingMessageRemoved) {
                 setMessages(prev => prev.filter(msg => msg.sender !== 'loading'));
            }
            setIsFetching(false); // Mark fetching as complete
            if (abortControllerRef.current === controller) {
                 abortControllerRef.current = null;
            }
        }
    };

    performFetch();

    return () => {
        console.log("Effect cleanup: Aborting fetch if still active.");
        controller.abort();
        if (abortControllerRef.current === controller) {
             abortControllerRef.current = null;
        }
    };
  }, [requestNonce, company]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
          abortControllerRef.current.abort();
      }
    };
  }, []);


  return (
    <div className="flex justify-center items-center min-h-screen bg-muted/40">
        <div className="flex flex-col h-screen w-full max-w-4xl bg-background text-foreground border-x">
            <header className="p-4 border-b text-center">
                <h1 className="text-xl font-semibold">종목분석</h1>
            </header>

            {/* Chat Area */}
            <div className="flex-grow overflow-y-auto p-4 space-y-4">
                {messages.map((msg) => (
                    <ChatMessageBubble key={msg.id} sender={msg.sender} text={msg.text} />
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area Container */}
            {/* Removed vertical padding and internal padding */}
            <div className="sticky bottom-0 px-6 py-6 bg-background border-t">
                <Card className="shadow-md">
                    <CardContent className="p-4"> {/* Removed internal padding */}
                        <form onSubmit={handleSubmit} className="flex flex-row gap-2 items-center">
                            <Input
                                type="text"
                                value={company}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCompany(e.target.value)}
                                placeholder="Company Name (e.g., Apple)"
                                className="flex-grow border-0 outline-none shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 h-8 px-2" // Kept height at h-4
                                required
                                disabled={isFetching} // Disable input while fetching
                            />
                            {/* Override button size with direct height class */}
                            <Button type="submit" disabled={!company || isFetching} className="h-8">
                                {isFetching ? "..." : "Send"}
                            </Button>
                            {isFetching && ( // Show stop button only when fetching
                                <Button type="button" variant="destructive" onClick={stopStreaming} className="h-8">
                                    Stop
                                </Button>
                            )}
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    </div>
  );
}
