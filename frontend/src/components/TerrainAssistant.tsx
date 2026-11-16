import React from 'react';
import { Bot, Send } from 'lucide-react';

/*
 * Isolated from the terrain implementation so a real assistant can replace
 * this prototype in a later phase.
 */
export default function TerrainAssistant({
  welcomeMessage,
}: {
  welcomeMessage: string;
}) {
  const [messages, setMessages] = React.useState([
    { user: '', ai: welcomeMessage },
  ]);
  const [input, setInput] = React.useState('');

  React.useEffect(() => {
    setMessages([{ user: '', ai: welcomeMessage }]);
  }, [welcomeMessage]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim()) return;

    setMessages((current) => [
      ...current,
      {
        user: input,
        ai: `This prototype assistant cannot evaluate "${input}" yet. Terrain controls remain available.`,
      },
    ]);
    setInput('');
  };

  return (
    <>
      <div className="p-4 border-b border-stone-800 flex items-center gap-2">
        <Bot size={16} className="text-green-500" />
        <h2 className="text-xs font-bold text-stone-500 tracking-widest">AI ASSISTANT (PROTOTYPE)</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-stone-800">
        {messages.map((message, index) => (
          <div key={index} className="space-y-3">
            {message.user && (
              <div className="bg-stone-800 p-3 rounded-lg rounded-br-none text-sm ml-8 text-stone-200 border border-stone-700">
                {message.user}
              </div>
            )}
            {message.ai && (
              <div className="bg-green-900/20 p-3 rounded-lg rounded-bl-none text-sm mr-8 text-green-100 border border-green-900/30 flex gap-3">
                <Bot size={16} className="text-green-500 shrink-0 mt-1" />
                <p className="leading-relaxed">{message.ai}</p>
              </div>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t border-stone-800 flex gap-2 bg-stone-900/50">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about terrain (prototype)"
          className="flex-1 bg-stone-950 border border-stone-800 rounded px-3 py-2 text-sm text-stone-200 outline-none focus:border-green-800 transition-colors placeholder:text-stone-600"
        />
        <button type="submit" className="bg-green-800 hover:bg-green-700 p-2 rounded text-green-50 transition-colors" aria-label="Send prototype message">
          <Send size={16} />
        </button>
      </form>
    </>
  );
}
