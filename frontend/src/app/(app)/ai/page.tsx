"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, User, Loader2 } from "lucide-react";
import { chatStream } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function AIConversationPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "你好！我是标标 AI 助手 🤖 可以为你解答标书编制、评分标准、工艺方案等问题。请问有什么可以帮你的？",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    // 添加用户消息
    const userMsg: Message = { role: "user", content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    // 添加空的 AI 回复占位
    const aiMsg: Message = { role: "assistant", content: "", timestamp: new Date() };
    setMessages((prev) => [...prev, aiMsg]);

    try {
      const response = await chatStream({ message: text });

      if (!response.ok) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content = "⚠️ 请求失败，请稍后重试。";
          return updated;
        });
        setIsStreaming(false);
        return;
      }

      // 流式读取 SSE
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") continue;
              try {
                const parsed = JSON.parse(data);
                const chunk = parsed.content || parsed.text || data;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content += chunk;
                  return [...updated];
                });
              } catch {
                // 纯文本 chunk
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content += data;
                  return [...updated];
                });
              }
            }
          }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content = `⚠️ 连接失败: ${err instanceof Error ? err.message : "未知错误"}`;
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen">
        {/* 顶栏 */}
        <div className="h-14 px-6 flex items-center border-b border-[var(--border-subtle)] shrink-0">
          <h1 className="text-sm font-semibold flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--primary)]" />
            AI 对话
          </h1>
          <span className="ml-3 text-xs text-[var(--text-tertiary)] bg-[var(--bg-surface)] px-2 py-0.5 rounded">
            标书编制智能助手
          </span>
        </div>

        {/* 消息区域 */}
        <div className="flex-1 overflow-auto px-6 py-6 space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center shrink-0">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
              )}
              <div
                className={`max-w-[70%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-[var(--primary)] text-white"
                    : "bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)]"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content || (isStreaming && i === messages.length - 1 ? "思考中..." : "")}</div>
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-[var(--text-secondary)]" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="shrink-0 px-6 pb-6 pt-2">
          <div className="flex gap-3 items-end bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl px-4 py-3 focus-within:border-[var(--primary)] transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入问题，如：市政道路工程的施工方案要点..."
              rows={1}
              className="flex-1 bg-transparent text-sm text-white placeholder:text-[var(--text-tertiary)] resize-none outline-none max-h-32"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                input.trim() && !isStreaming
                  ? "bg-[var(--primary)] text-white hover:opacity-90"
                  : "bg-[var(--bg-elevated)] text-[var(--text-tertiary)]"
              }`}
            >
              {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-center text-[10px] text-[var(--text-tertiary)] mt-2">
            AI 回复仅供参考，重要内容请以官方文件为准
          </p>
        </div>
      </div>
  );
}
