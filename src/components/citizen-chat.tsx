"use client";

import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";
import { Send, Bot, User, Globe } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  city?: string;
  aqi?: number;
  category?: string;
  suggestions?: string[];
  poweredBy?: string;
}

const LANGUAGES = [
  { code: "en", label: "English", flag: "EN" },
  { code: "hi", label: "हिन्दी", flag: "HI" },
  { code: "ta", label: "தமிழ்", flag: "TA" },
  { code: "kn", label: "ಕನ್ನಡ", flag: "KN" },
  { code: "te", label: "తెలుగు", flag: "TE" },
];

export default function CitizenChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [currentCity, setCurrentCity] = useState<string | undefined>();
  const scrollRef = useRef<HTMLDivElement>(null);

  const greetedRef = useRef(false);
  useEffect(() => {
    if (!greetedRef.current) {
      greetedRef.current = true;
      handleSend("hello", true);
    }
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string, isGreeting = false) {
    const msg = text || input.trim();
    if (!msg) return;

    if (!isGreeting) {
      setMessages((prev) => [
        ...prev,
        { id: `u-${Date.now()}`, role: "user", content: msg },
      ]);
    }
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(msg, language, currentCity);
      if (res.city) setCurrentCity(res.city);

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: res.response,
          city: res.city,
          aqi: res.aqi,
          category: res.category,
          suggestions: res.suggestions,
          poweredBy: res.powered_by,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: `e-${Date.now()}`, role: "assistant", content: "Sorry, I couldn't process that. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function getCategoryColor(cat?: string) {
    const colors: Record<string, string> = {
      good: "#22c55e", satisfactory: "#84cc16", moderate: "#eab308",
      poor: "#f97316", very_poor: "#ef4444", severe: "#991b1b",
    };
    return colors[cat || ""] || "#71717a";
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold">VayuBudhi Advisor</span>
        </div>
        <div className="flex items-center gap-1">
          <Globe className="w-3 h-3 text-zinc-500" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="text-xs bg-zinc-800 border border-zinc-700 rounded px-1.5 py-0.5 text-zinc-300 focus:outline-none focus:border-cyan-500"
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>{l.flag} {l.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5 text-cyan-400" />
              </div>
            )}
            <div className={`max-w-[85%] ${msg.role === "user"
              ? "bg-cyan-600/30 border border-cyan-500/30 rounded-2xl rounded-tr-md px-3 py-2"
              : "bg-zinc-800/80 border border-zinc-700/50 rounded-2xl rounded-tl-md px-3 py-2"
            }`}>
              {msg.aqi !== undefined && msg.city && (
                <div className="flex items-center gap-2 mb-1.5 pb-1.5 border-b border-zinc-700/50">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getCategoryColor(msg.category) }} />
                  <span className="text-[10px] font-semibold text-zinc-400">
                    {msg.city} AQI {msg.aqi}
                  </span>
                  {msg.poweredBy === "gemini" && (
                    <span className="text-[9px] bg-purple-500/20 text-purple-400 px-1 rounded">AI</span>
                  )}
                </div>
              )}
              <p className="text-sm text-zinc-200 whitespace-pre-line">{msg.content}</p>

              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-2 pt-2 border-t border-zinc-700/50 flex flex-wrap gap-1">
                  {msg.suggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => { setInput(s); handleSend(s); }}
                      className="text-[10px] bg-zinc-700/50 hover:bg-zinc-600/50 text-cyan-300 px-2 py-1 rounded-full transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5 text-zinc-400" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
              <Bot className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            </div>
            <div className="bg-zinc-800/80 border border-zinc-700/50 rounded-2xl rounded-tl-md px-4 py-2">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-2 border-t border-zinc-800">
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={language === "hi" ? "अपना सवाल पूछें..." : "Ask about air quality..."}
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-cyan-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white rounded-lg transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
