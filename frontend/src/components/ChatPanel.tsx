import { useState, useRef, useEffect } from "react";
import { Bot, Send, X } from "lucide-react";
import {
  fetchRiskOverview,
  fetchSPOFs,
  fetchCriticality,
  runSimulation,
  fetchRecommendations,
} from "../api/client";

interface Message {
  id: number;
  role: "user" | "assistant";
  text: string;
}

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const WELCOME =
  "Hello! I'm **ShieldAI**, your supply chain risk assistant. Try asking me to:\n\n" +
  "- **summarize** risks\n" +
  "- show **riskiest** suppliers\n" +
  "- **simulate S042**\n" +
  "- **recommend** actions";

const FALLBACK =
  "I can help with:\n\n" +
  "- **summarize** — risk overview\n" +
  "- **riskiest** — top critical suppliers\n" +
  "- **simulate [ID]** — Monte Carlo simulation\n" +
  "- **recommend** — priority actions";

function fmt(n: number): string {
  if (n >= 1_000_000) return `€${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `€${(n / 1_000).toFixed(0)}K`;
  return `€${n.toFixed(0)}`;
}

async function handleCommand(input: string): Promise<string> {
  const lower = input.toLowerCase().trim();

  // ── summarize / overview ──
  if (lower.includes("summarize") || lower.includes("overview") || lower.includes("summary")) {
    try {
      const [risk, spofs] = await Promise.all([fetchRiskOverview(), fetchSPOFs()]);
      return (
        `Your supply chain has **${risk.total_suppliers} suppliers** across 3 tiers ` +
        `with an average risk score of **${risk.avg_risk.toFixed(1)}/100**.\n\n` +
        `Risk breakdown: ${risk.categories.CRITICAL ?? 0} Critical, ` +
        `${risk.categories.HIGH ?? 0} High, ` +
        `${risk.categories.MEDIUM ?? 0} Medium, ` +
        `${risk.categories.LOW ?? 0} Low.\n\n` +
        `**${spofs.length} Single Points of Failure** detected — these suppliers ` +
        `have no backup and pose significant disruption risk.`
      );
    } catch {
      return "Sorry, I couldn't fetch the risk summary right now. Is the backend running?";
    }
  }

  // ── riskiest / critical ──
  if (lower.includes("riskiest") || lower.includes("critical")) {
    try {
      const { items } = await fetchCriticality(5);
      let msg = "Here are your **top 5 most critical** suppliers:\n\n";
      items.forEach((s, i) => {
        msg +=
          `${i + 1}. **${s.name}** (${s.supplier_id}) — Tier ${s.tier}, ` +
          `Risk: ${s.propagated_risk.toFixed(1)} (${s.risk_category}), ` +
          `Exposure: ${fmt(s.total_revenue_exposure)}\n`;
      });
      return msg;
    } catch {
      return "Sorry, I couldn't fetch criticality data right now.";
    }
  }

  // ── simulate <ID> ──
  const simMatch = lower.match(/simulate\s+(s\d+)/i);
  if (simMatch) {
    const supplierId = simMatch[1].toUpperCase();
    try {
      const result = await runSimulation({
        target_supplier: supplierId,
        duration_days: 30,
        iterations: 5000,
        scenario_type: "single_node",
      });
      return (
        `I ran a **5,000-iteration Monte Carlo simulation** for supplier ${supplierId} over 30 days:\n\n` +
        `Mean revenue impact: **${fmt(result.mean)}** | ` +
        `Worst case: **${fmt(result.max)}** | ` +
        `95th percentile: **${fmt(result.p95)}**\n\n` +
        `**${result.affected_suppliers_count} suppliers** and ` +
        `**${result.affected_products.length} products** would be affected.`
      );
    } catch {
      return `Sorry, I couldn't run a simulation for ${supplierId}. Make sure it's a valid supplier ID (e.g. S042).`;
    }
  }

  // ── recommend ──
  if (lower.includes("recommend") || lower.includes("what should i do")) {
    try {
      const recs = await fetchRecommendations("CRITICAL");
      const top = recs.slice(0, 3);
      if (top.length === 0) {
        const allRecs = await fetchRecommendations();
        const topAll = allRecs.slice(0, 3);
        if (topAll.length === 0) return "No recommendations available right now.";
        let msg = "Here are your **top priority actions**:\n\n";
        topAll.forEach((r, i) => {
          msg += `${i + 1}. **${r.supplier_name}** — ${r.action} (${r.timeline}). ${r.reason}\n`;
        });
        return msg;
      }
      let msg = "Here are your **top priority actions**:\n\n";
      top.forEach((r, i) => {
        msg += `${i + 1}. **${r.supplier_name}** — ${r.action} (${r.timeline}). ${r.reason}\n`;
      });
      return msg;
    } catch {
      return "Sorry, I couldn't fetch recommendations right now.";
    }
  }

  // ── fallback ──
  return FALLBACK;
}

function renderMarkdown(text: string) {
  // Minimal markdown: **bold** and newlines
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
    }
    // Convert \n to <br>
    const lines = part.split("\n");
    return lines.map((line, j) => (
      <span key={`${i}-${j}`}>
        {j > 0 && <br />}
        {line}
      </span>
    ));
  });
}

export default function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, role: "assistant", text: WELCOME },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  let nextId = useRef(1);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  const send = async () => {
    const text = inputValue.trim();
    if (!text || isTyping) return;

    const userMsg: Message = { id: nextId.current++, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    const response = await handleCommand(text);

    // Fake typing delay
    await new Promise((r) => setTimeout(r, 1000));

    const botMsg: Message = { id: nextId.current++, role: "assistant", text: response };
    setMessages((prev) => [...prev, botMsg]);
    setIsTyping(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-24 right-6 z-50 w-[400px] h-[500px] flex flex-col rounded-xl border border-shield-border bg-shield-bg shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-shield-border bg-shield-surface">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-shield-accent/20 flex items-center justify-center">
            <Bot size={18} className="text-shield-accent" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">ShieldAI Assistant</h3>
            <p className="text-xs text-shield-muted">Supply chain intelligence</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-shield-muted hover:text-white p-1 rounded transition-colors"
          aria-label="Close chat"
        >
          <X size={18} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-6 h-6 rounded-full bg-shield-accent/20 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                <Bot size={14} className="text-shield-accent" />
              </div>
            )}
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-shield-accent text-white"
                  : "bg-shield-surface text-shield-muted"
              }`}
            >
              {renderMarkdown(msg.text)}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="w-6 h-6 rounded-full bg-shield-accent/20 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
              <Bot size={14} className="text-shield-accent" />
            </div>
            <div className="bg-shield-surface rounded-lg px-4 py-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-shield-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-shield-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-shield-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-shield-border bg-shield-surface">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about your supply chain..."
            className="flex-1 bg-shield-bg border border-shield-border rounded-lg px-3 py-2 text-sm text-white placeholder-shield-muted focus:outline-none focus:border-shield-accent transition-colors"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className="w-9 h-9 rounded-lg bg-shield-accent hover:bg-orange-600 disabled:opacity-40 disabled:hover:bg-shield-accent text-white flex items-center justify-center transition-colors"
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
