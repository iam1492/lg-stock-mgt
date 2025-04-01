'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // For GitHub Flavored Markdown (tables, etc.)

// Define an interface for the expected JSON structure
interface StreamData {
  content: string;
  // Add other potential fields if needed
}

export default function Home() {
  const [company, setCompany] = useState('');
  const [responses, setResponses] = useState<string[]>([]); // State to hold array of content strings
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setResponses([]); // Clear previous responses

    try {
      // Generate userInput based on company *before* the fetch call
      const generatedUserInput = `Do a research and Analyze ${company} stock.`;

      const res = await fetch('http://localhost:8080/stream_endpoint', { // Point to the backend server on port 8080
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Send data matching the StreamRequest model directly
          company: company,
          user_input: generatedUserInput, // Use generated input
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
      let buffer = ''; // Buffer to hold incomplete JSON strings

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });

          // Process buffer line by line (assuming JSON objects are newline-separated and prefixed with "data: ")
          let newlineIndex;
          while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
            const line = buffer.slice(0, newlineIndex).trim();
            buffer = buffer.slice(newlineIndex + 1); // Keep the rest for next iteration

            if (line.startsWith('data: ')) { // Process only lines starting with "data: "
              const jsonString = line.substring(6).trim(); // Remove "data: " prefix
              if (jsonString) {
                try {
                  const parsedData: StreamData = JSON.parse(jsonString);
                  if (parsedData.content) {
                    setResponses(prev => [...prev, parsedData.content]); // Add new content to the array
                  }
                } catch (parseError) {
                  console.warn('Failed to parse JSON chunk:', jsonString, parseError);
                  // Optionally handle non-JSON lines or parse errors differently
                }
              }
            } else if (line) {
              console.log("Received non-data line:", line); // Log other lines if needed
            }
          }
        }
      }
      // Process any remaining data in the buffer after the stream ends
      if (buffer.trim().startsWith('data: ')) {
         const jsonString = buffer.substring(6).trim();
         if (jsonString) {
           try {
              const parsedData: StreamData = JSON.parse(jsonString);
              if (parsedData.content) {
                setResponses(prev => [...prev, parsedData.content]);
              }
            } catch (parseError) {
              console.warn('Failed to parse final JSON chunk:', jsonString, parseError);
            }
         }
      }
    } catch (error) {
      console.error('Error fetching stream:', error);
      // Display error in a user-friendly way, maybe add to responses array
      setResponses([`**Error:** ${error instanceof Error ? error.message : 'Unknown error'}`]);
    } finally {
      setIsLoading(false); // Stop loading indicator once stream is finished or errored
    }
  };

  // Dark Mode UI inspired by the article, adapted for this structure
  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 sm:p-12 bg-gray-900 text-gray-100">
      <h1 className="text-3xl sm:text-4xl font-bold mb-8 text-gray-50">Stock Analysis Agent</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-xl bg-gray-800 p-6 sm:p-8 rounded-lg shadow-xl border border-gray-700">
        <div className="mb-6"> {/* Increased bottom margin */}
          <label htmlFor="company" className="block text-gray-300 text-sm font-bold mb-2">
            Company Name:
          </label>
          <input
            type="text"
            id="company"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            required
            className="shadow appearance-none border border-gray-600 bg-gray-700 rounded w-full py-3 px-4 text-gray-100 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500"
            placeholder="e.g., Samsung Electronics, Apple, LG Electronics"
          />
        </div>
        {/* Removed userInput textarea */}
        <div className="flex items-center justify-end"> {/* Align button to the right */}
          <button
            type="submit"
            disabled={isLoading || !company} // Disable if loading or company is empty
            className={`bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out ${isLoading || !company ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </>
            ) : (
              'Analyze Stock'
            )}
          </button>
        </div>
      </form>

      {/* Response Area */}
      {(isLoading || responses.length > 0) && ( // Show container if loading or responses exist
        <div className="w-full max-w-xl mt-8 bg-gray-800 p-6 rounded-lg shadow-xl border border-gray-700">
          <h2 className="text-xl font-semibold mb-4 text-gray-200">Analysis Result:</h2>
          {/* Show loading indicator specifically when loading AND no responses have arrived yet */}
          {isLoading && responses.length === 0 && (
            <div className="text-center text-gray-400 py-4">
              <svg className="animate-spin h-5 w-5 text-blue-400 inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                 <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Fetching analysis... please wait.
            </div>
          )}
          {/* Render each response content as Markdown */}
          {responses.map((content, index) => (
            <div key={index} className="markdown-content mb-6 p-4 border border-gray-700 rounded bg-gray-850 shadow-inner prose prose-invert prose-sm max-w-none"> {/* Moved prose classes here */}
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </div>
          ))}
          {/* Optional: Show a message when loading is finished if needed */}
          {/* {!isLoading && responses.length > 0 && (
            <p className="text-sm text-gray-500 mt-4 text-center">Analysis complete.</p>
          )} */}
        </div>
      )}
    </main>
  );
}

// Add some basic prose styling overrides if needed, or rely on Tailwind prose plugin
// You might need to adjust globals.css if using Tailwind Prose plugin
