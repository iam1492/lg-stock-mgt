'use client';

import React, { useState } from 'react';

export default function Home() {
  const [company, setCompany] = useState('');
  const [userInput, setUserInput] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setResponse(''); // Clear previous response

    try {
      const res = await fetch('http://localhost:8080/stream_endpoint', { // Point to the backend server on port 8080
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Send data matching the StreamRequest model directly
          company: company,
          user_input: userInput,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      if (!res.body) {
        throw new Error('Response body is null');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedResponse = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          // Process the chunk - assuming simple text stream for now
          // You might need more complex parsing if the stream format is different (e.g., JSON events)
          accumulatedResponse += chunk;
          setResponse(accumulatedResponse); // Update state incrementally
        }
      }
    } catch (error) {
      console.error('Error fetching stream:', error);
      setResponse(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-12 bg-gray-50">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Stock Agent Interface</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-lg bg-white p-8 rounded-lg shadow-md">
        <div className="mb-4">
          <label htmlFor="company" className="block text-gray-700 text-sm font-bold mb-2">
            Company Name:
          </label>
          <input
            type="text"
            id="company"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            required
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="e.g., Samsung Electronics"
          />
        </div>
        <div className="mb-6">
          <label htmlFor="userInput" className="block text-gray-700 text-sm font-bold mb-2">
            Your Question:
          </label>
          <textarea
            id="userInput"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            required
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-24 resize-none"
            placeholder="e.g., What were the key financial highlights last quarter?"
          />
        </div>
        <div className="flex items-center justify-between">
          <button
            type="submit"
            disabled={isLoading}
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? 'Loading...' : 'Ask Agent'}
          </button>
        </div>
      </form>

      {response && (
        <div className="w-full max-w-lg mt-8 bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Response:</h2>
          {/* Using whitespace-pre-wrap to preserve formatting like newlines */}
          <pre className="text-gray-800 whitespace-pre-wrap break-words">{response}</pre>
        </div>
      )}
    </main>
  );
}
