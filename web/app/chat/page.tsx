'use client';

import { useEffect, useState, useRef } from 'react';
import { Send, Mic, Search, Plus, MoreVertical, Smile, Copy, Bookmark, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { streamChat, chatApi } from '@/lib/api';
import { useStore } from '@/lib/store';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDistance } from 'date-fns';

export default function ChatPage() {
  const {
    currentProject,
    messages,
    sessionId,
    isStreaming,
    addMessage,
    updateLastMessage,
    setSessionId,
    setIsStreaming,
  } = useStore();

  const [input, setInput] = useState('');
  const [showHistory, setShowHistory] = useState(true);
  const [mode, setMode] = useState('brief');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sessionId) {
      setSessionId(`session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
    }
  }, [sessionId, setSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      role: 'user' as const,
      content: input,
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');
    setIsStreaming(true);

    addMessage({
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    });

    try {
      const projectId = currentProject?.id || 'default-project';
      
      for await (const event of streamChat(projectId, input, sessionId, mode)) {
        if (event.type === 'token') {
          updateLastMessage(event.content);
        } else if (event.type === 'citations') {
          // Handle citations
        } else if (event.type === 'error') {
          updateLastMessage(`\n\n**Error:** ${event.message}`);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      updateLastMessage('\n\n**Error:** Failed to get response');
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#1a1b1e]">
      {/* Chat History Sidebar */}
      {showHistory && (
        <div className="w-80 bg-[#2b2d31] border-r border-[#3f4147] flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-[#3f4147] flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[#f2f3f5] flex items-center gap-2">
              <Sparkles size={20} className="text-[#23a55a]" />
              My Chats
            </h2>
            <div className="flex items-center gap-2">
              <button className="w-8 h-8 rounded-lg bg-[#23a55a] hover:bg-[#1f8f4d] text-white flex items-center justify-center transition-colors">
                <Plus size={18} />
              </button>
              <button className="w-8 h-8 rounded-lg hover:bg-[#383a40] text-[#b5bac1] flex items-center justify-center transition-colors">
                <MoreVertical size={18} />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 px-4 py-3 border-b border-[#3f4147]">
            <button className="flex-1 px-3 py-2 rounded-lg bg-[#383a40] text-[#23a55a] text-sm font-medium flex items-center justify-center gap-2">
              <span>💬</span>
              CHATS
              <span className="text-xs bg-[#23a55a] text-white px-1.5 py-0.5 rounded">24</span>
            </button>
            <button className="flex-1 px-3 py-2 rounded-lg hover:bg-[#383a40] text-[#b5bac1] text-sm font-medium flex items-center justify-center gap-2">
              <span>📌</span>
              SAVED
              <span className="text-xs bg-[#4e5058] text-[#b5bac1] px-1.5 py-0.5 rounded">24</span>
            </button>
          </div>

          {/* Search */}
          <div className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#80848e]" size={18} />
              <input
                type="text"
                placeholder="Search..."
                className="w-full pl-10 pr-4 py-2 bg-[#1a1b1e] border border-[#3f4147] rounded-lg text-[#f2f3f5] placeholder-[#80848e] focus:outline-none focus:border-[#23a55a] transition-colors"
              />
            </div>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto px-2">
            {[
              {
                title: 'Strategic Analysis 2025',
                preview: 'What are the key technology trends...',
                time: '2 min ago',
                active: true,
              },
              {
                title: 'Market Research Report',
                preview: 'Can you help me analyze the competitive...',
                time: '1 hour ago',
                active: false,
              },
              {
                title: 'SWOT Analysis',
                preview: 'Generate a SWOT analysis for...',
                time: 'Yesterday',
                active: false,
              },
            ].map((chat, idx) => (
              <button
                key={idx}
                className={`w-full p-3 rounded-lg mb-2 text-left transition-colors ${
                  chat.active
                    ? 'bg-[#383a40] border border-[#4e5058]'
                    : 'hover:bg-[#383a40]'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-[#23a55a] mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-medium text-[#f2f3f5] truncate">{chat.title}</h3>
                      <span className="text-xs text-[#80848e] flex-shrink-0 ml-2">{chat.time}</span>
                    </div>
                    <p className="text-xs text-[#b5bac1] line-clamp-2">{chat.preview}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-[#313338]">
        {/* Header */}
        <div className="h-16 bg-[#2b2d31] border-b border-[#3f4147] flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="w-8 h-8 rounded-lg hover:bg-[#383a40] text-[#b5bac1] flex items-center justify-center transition-colors"
            >
              {showHistory ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
            </button>
            <h1 className="text-lg font-semibold text-[#f2f3f5]">
              {currentProject?.name || 'New Chat'}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button className="w-8 h-8 rounded-lg hover:bg-[#383a40] text-[#b5bac1] flex items-center justify-center transition-colors">
              <Search size={18} />
            </button>
            <button className="w-8 h-8 rounded-lg hover:bg-[#383a40] text-[#b5bac1] flex items-center justify-center transition-colors">
              <MoreVertical size={18} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-teal-500 to-green-600 flex items-center justify-center mx-auto mb-4">
                  <Sparkles size={32} className="text-white" />
                </div>
                <h2 className="text-2xl font-semibold text-[#f2f3f5] mb-2">
                  Start a Conversation
                </h2>
                <p className="text-[#b5bac1]">
                  Ask questions about your documents and get AI-powered insights with citations
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message, idx) => (
                <div key={idx} className="message-enter">
                  {message.role === 'user' ? (
                    /* User Message */
                    <div className="flex gap-3 items-start">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center flex-shrink-0 text-white font-semibold text-sm">
                        Y
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-[#f2f3f5]">You</span>
                          <span className="text-xs text-[#80848e]">
                            {formatDistance(new Date(message.timestamp), new Date(), {
                              addSuffix: true,
                            })}
                          </span>
                        </div>
                        <div className="bg-[#383a40] rounded-lg p-4 text-[#f2f3f5]">
                          {message.content}
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Assistant Message */
                    <div className="flex gap-3 items-start">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-green-600 flex items-center justify-center flex-shrink-0">
                        <Sparkles size={16} className="text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-[#f2f3f5]">Response</span>
                            <span className="text-xs text-[#80848e]">
                              {formatDistance(new Date(message.timestamp), new Date(), {
                                addSuffix: true,
                              })}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-[#80848e]">1/3</span>
                          </div>
                        </div>
                        <div className="bg-[#2b2d31] rounded-lg p-4 border border-[#3f4147]">
                          <div className="prose prose-invert max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {message.content}
                            </ReactMarkdown>
                          </div>
                          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-[#3f4147]">
                            <button className="px-3 py-1.5 rounded-lg hover:bg-[#383a40] text-[#b5bac1] text-sm flex items-center gap-2 transition-colors">
                              <Smile size={14} />
                            </button>
                            <button className="px-3 py-1.5 rounded-lg hover:bg-[#383a40] text-[#b5bac1] text-sm flex items-center gap-2 transition-colors">
                              <Smile size={14} className="rotate-180" />
                            </button>
                            <div className="flex-1" />
                            <button className="px-3 py-1.5 rounded-lg hover:bg-[#383a40] text-[#b5bac1] text-sm flex items-center gap-2 transition-colors">
                              <Sparkles size={14} />
                              Generate Response
                            </button>
                            <button className="px-3 py-1.5 rounded-lg hover:bg-[#383a40] text-[#b5bac1] text-sm flex items-center gap-2 transition-colors">
                              <Copy size={14} />
                              Copy
                            </button>
                            <button className="px-3 py-1.5 rounded-lg hover:bg-[#383a40] text-[#b5bac1] text-sm flex items-center gap-2 transition-colors">
                              <Bookmark size={14} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {isStreaming && (
                <div className="flex gap-3 items-start message-enter">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-green-600 flex items-center justify-center flex-shrink-0">
                    <Sparkles size={16} className="text-white animate-pulse" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-[#f2f3f5]">Response</span>
                      <span className="text-xs text-[#80848e]">Just now</span>
                    </div>
                    <div className="bg-[#2b2d31] rounded-lg p-4 border border-[#3f4147]">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-[#23a55a] pulse" />
                        <div className="w-2 h-2 rounded-full bg-[#23a55a] pulse" style={{ animationDelay: '0.2s' }} />
                        <div className="w-2 h-2 rounded-full bg-[#23a55a] pulse" style={{ animationDelay: '0.4s' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-6 bg-[#2b2d31] border-t border-[#3f4147]">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 bg-[#383a40] rounded-xl p-2 border border-[#4e5058] focus-within:border-[#23a55a] transition-colors">
              <button className="w-10 h-10 rounded-lg hover:bg-[#404249] text-[#b5bac1] flex items-center justify-center transition-colors flex-shrink-0">
                <Plus size={20} />
              </button>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder="Ask questions, or type '/' for commands"
                disabled={isStreaming}
                className="flex-1 bg-transparent text-[#f2f3f5] placeholder-[#80848e] focus:outline-none disabled:opacity-50"
              />
              <button className="w-10 h-10 rounded-lg hover:bg-[#404249] text-[#b5bac1] flex items-center justify-center transition-colors flex-shrink-0">
                <Mic size={20} />
              </button>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isStreaming}
                className="w-10 h-10 rounded-lg bg-[#23a55a] hover:bg-[#1f8f4d] text-white flex items-center justify-center transition-colors flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="text-xs text-[#80848e] text-center mt-2">
              Press Enter to send, Shift + Enter for new line
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
