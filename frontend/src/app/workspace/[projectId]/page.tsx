"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  FileText,
  FolderTree,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Save,
  Download,
  Send,
  Bot,
  User,
  Upload,
  FileSearch,
  Brain,
  Shield,
  Settings,
  X,
  Menu,
  AlertTriangle,
  BarChart3,
  Check,
  XCircle,
  Loader2,
} from "lucide-react";

/* ========================================
   Step 定义
   ======================================== */
const STEPS = [
  { num: 1, title: "标书设置", icon: Settings },
  { num: 2, title: "招标解读", icon: FileSearch },
  { num: 3, title: "目录生成", icon: FolderTree },
  { num: 4, title: "内容生成", icon: Brain },
  { num: 5, title: "审查导出", icon: Shield },
];

/* ========================================
   Mock 目录数据
   ======================================== */
const mockOutline = [
  { id: "1", title: "第一章 投标函及投标函附录", depth: 0 },
  { id: "2", title: "第二章 法定代表人身份证明", depth: 0 },
  { id: "3", title: "第三章 技术标", depth: 0 },
  { id: "3-1", title: "3.1 工程概况", depth: 1 },
  { id: "3-2", title: "3.2 施工组织设计", depth: 1 },
  { id: "3-3", title: "3.3 施工进度计划", depth: 1 },
  { id: "3-4", title: "3.4 质量保证措施", depth: 1 },
  { id: "3-5", title: "3.5 安全文明施工", depth: 1 },
  { id: "4", title: "第四章 商务标", depth: 0 },
  { id: "5", title: "第五章 资信标", depth: 0 },
];

/* ========================================
   Mock AI 对话
   ======================================== */
const mockMessages = [
  { role: "assistant", content: "你好！我已准备好协助您编写标书。请告诉我需要什么帮助？" },
];

/* ========================================
   Step 1 — 标书设置
   ======================================== */
function Step1Form() {
  const [bidType, setBidType] = useState("NORMAL_BID_DOC");
  const [projectName, setProjectName] = useState("");
  const [industry, setIndustry] = useState("municipal_road");

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-lg font-semibold mb-1">标书基本设置</h2>
        <p className="text-sm text-[var(--text-tertiary)]">配置标书类型和项目基本信息</p>
      </div>

      {/* 标书类型 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">标书类型</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: "NORMAL_BID_DOC", label: "工程类", desc: "技术标/资信标" },
            { value: "SERVICE_BID_DOC", label: "服务类", desc: "服务方案标" },
            { value: "GOODS_BID_DOC", label: "货物类", desc: "设备采购标" },
          ].map((type) => (
            <button
              key={type.value}
              onClick={() => setBidType(type.value)}
              className={`p-4 rounded-xl border text-left transition-all ${
                bidType === type.value
                  ? "border-[var(--primary)] bg-[var(--primary-glow)]"
                  : "border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)]"
              }`}
            >
              <p className="font-medium text-sm">{type.label}</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{type.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* 项目名称 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">项目名称</label>
        <input
          type="text"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="如：XX市政道路改造工程施工标"
          className="w-full px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm"
        />
      </div>

      {/* 工程行业 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">工程行业</label>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="w-full px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm appearance-none"
        >
          <option value="municipal_road">市政道路工程</option>
          <option value="building">房屋建筑工程</option>
          <option value="water">水利水电工程</option>
          <option value="bridge">桥梁工程</option>
          <option value="landscape">园林绿化工程</option>
          <option value="decoration">装饰装修工程</option>
        </select>
      </div>

      {/* 招标方式 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">招标方式</label>
        <div className="flex gap-3">
          {["公开招标", "邀请招标"].map((method) => (
            <label key={method} className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
              <input type="radio" name="method" defaultChecked={method === "公开招标"} className="accent-[var(--primary)]" />
              {method}
            </label>
          ))}
        </div>
      </div>

      {/* 评标方法 */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">评标方法</label>
        <div className="flex gap-3">
          {["综合评估法", "经评审的最低投标价法", "性价比法"].map((m) => (
            <label key={m} className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
              <input type="radio" name="eval" defaultChecked={m === "综合评估法"} className="accent-[var(--primary)]" />
              {m}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ========================================
   Step 2 — 招标文件解读
   ======================================== */
function Step2Upload() {
  const [uploaded, setUploaded] = useState(false);
  const [parsing, setParsing] = useState(false);

  const handleUpload = () => {
    setUploaded(true);
    setParsing(true);
    // 模拟解析过程
    setTimeout(() => setParsing(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-lg font-semibold mb-1">上传招标文件</h2>
        <p className="text-sm text-[var(--text-tertiary)]">AI 将自动解析文件，提取废标红线和评分标准</p>
      </div>

      {/* 上传区域 */}
      {!uploaded ? (
        <div
          onClick={handleUpload}
          className="border-2 border-dashed border-[var(--border-default)] rounded-2xl p-12 text-center cursor-pointer hover:border-[var(--primary)] hover:bg-[var(--primary-glow)] transition-all group"
        >
          <Upload className="w-10 h-10 mx-auto text-[var(--text-tertiary)] group-hover:text-[var(--primary)] transition-colors mb-4" />
          <p className="font-medium text-[var(--text-secondary)] mb-1">点击上传或拖拽文件</p>
          <p className="text-xs text-[var(--text-tertiary)]">支持 PDF / Word / 扫描件</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* 已上传文件 */}
          <div className="flex items-center gap-3 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
            <FileText className="w-8 h-8 text-[var(--primary)]" />
            <div className="flex-1">
              <p className="text-sm font-medium">XX市政道路工程招标文件.pdf</p>
              <p className="text-xs text-[var(--text-tertiary)]">2.4 MB · PDF</p>
            </div>
            {parsing ? (
              <div className="flex items-center gap-2 text-xs text-[var(--primary)]">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                AI 解析中...
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-[var(--success)]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                解析完成
              </div>
            )}
          </div>

          {/* AI 解析结果概览 */}
          {!parsing && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Brain className="w-4 h-4 text-[var(--primary)]" />
                AI 解析结果
              </h3>

              {/* 废标红线 */}
              <div className="p-4 rounded-xl bg-[rgba(239,68,68,0.06)] border border-[rgba(239,68,68,0.15)]">
                <p className="text-sm font-medium text-[var(--danger)] flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-4 h-4" />
                  废标红线 (共 5 项)
                </p>
                <ul className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                  <li>• 投标保证金须在开标前到账</li>
                  <li>• 项目经理须具备市政公用工程一级建造师</li>
                  <li>• 投标有效期不少于 90 天</li>
                  <li>• 须提供近 3 年类似工程业绩不少于 2 项</li>
                  <li>• 联合体投标须提供联合体协议</li>
                </ul>
              </div>

              {/* 评分标准 */}
              <div className="p-4 rounded-xl bg-[rgba(99,102,241,0.06)] border border-[rgba(99,102,241,0.15)]">
                <p className="text-sm font-medium text-[var(--primary)] flex items-center gap-2 mb-2">
                  <BarChart3 className="w-4 h-4" />
                  评分标准
                </p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="p-2 rounded-lg bg-[var(--bg-elevated)] text-center">
                    <p className="text-[var(--primary)] font-bold text-lg">60</p>
                    <p className="text-[var(--text-tertiary)]">技术标</p>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-elevated)] text-center">
                    <p className="text-[var(--primary)] font-bold text-lg">25</p>
                    <p className="text-[var(--text-tertiary)]">商务标</p>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-elevated)] text-center">
                    <p className="text-[var(--primary)] font-bold text-lg">15</p>
                    <p className="text-[var(--text-tertiary)]">资信标</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}

/* ========================================
   Step 3/4/5 占位
   ======================================== */
function StepPlaceholder({ step }: { step: number }) {
  const info = STEPS[step - 1];
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-[var(--primary-glow)] flex items-center justify-center mb-4">
        <info.icon className="w-8 h-8 text-[var(--primary)]" />
      </div>
      <h2 className="text-lg font-semibold mb-2">{info.title}</h2>
      <p className="text-sm text-[var(--text-tertiary)] max-w-sm">
        此功能将在 Phase 2 中实现。完成前序步骤后可自动进入。
      </p>
    </div>
  );
}

/* ========================================
   AI 助手面板
   ======================================== */
function AIChatPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState(mockMessages);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, { role: "user", content: input }]);
    setInput("");
    // 模拟 AI 回复
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `收到您的需求：「${input}」。我正在为您处理...  \n\n> 💡 **提示**：这是 Demo 模式的模拟回复。正式版本将通过 SSE 流式输出真实 AI 内容。`,
        },
      ]);
    }, 800);
  };

  return (
    <div className="flex flex-col h-full border-l border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
      {/* 面板头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-[var(--primary)]" />
          <span className="text-sm font-semibold">AI 助手</span>
        </div>
        <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-white transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 审查概览 */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <p className="text-xs text-[var(--text-tertiary)] mb-2 font-medium">合规审查概览</p>
        <div className="flex gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(34,197,94,0.1)] text-xs text-[var(--success)]">
            <Check className="w-3 h-3" /> 合规 12
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(245,158,11,0.1)] text-xs text-[var(--warning)]">
            <AlertTriangle className="w-3 h-3" /> 警告 3
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(239,68,68,0.1)] text-xs text-[var(--danger)]">
            <XCircle className="w-3 h-3" /> 危险 1
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                msg.role === "assistant"
                  ? "bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)]"
                  : "bg-[var(--bg-surface)]"
              }`}
            >
              {msg.role === "assistant" ? (
                <Bot className="w-3.5 h-3.5 text-white" />
              ) : (
                <User className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
              )}
            </div>
            <div
              className={`max-w-[85%] p-3 rounded-xl text-sm leading-relaxed ${
                msg.role === "assistant"
                  ? "bg-[var(--bg-surface)] text-[var(--text-secondary)]"
                  : "bg-[var(--primary)] text-white"
              }`}
            >
              {msg.content}
            </div>
          </motion.div>
        ))}
      </div>

      {/* 输入框 */}
      <div className="p-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="输入指令或问题..."
            className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-sm text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all"
          />
          <button
            onClick={handleSend}
            className="w-8 h-8 rounded-lg bg-[var(--primary)] flex items-center justify-center hover:bg-[var(--primary-hover)] transition-colors"
          >
            <Send className="w-3.5 h-3.5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ========================================
   工作台主页面
   ======================================== */
export default function WorkspacePage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [showChat, setShowChat] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);

  const handleNext = () => setCurrentStep((s) => Math.min(s + 1, 5));
  const handlePrev = () => setCurrentStep((s) => Math.max(s - 1, 1));

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-base)]">
      {/* TopBar */}
      <header className="shrink-0 h-12 glass border-b border-[var(--border-subtle)] flex items-center justify-between px-4 z-40">
        <div className="flex items-center gap-3">
          <button onClick={() => (window.location.href = "/dashboard")} className="text-[var(--text-tertiary)] hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-semibold">XX市政道路工程技术标</span>
          </div>
          <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
            已保存
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all md:hidden"
          >
            <Menu className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowChat(!showChat)}
            className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all"
          >
            <Bot className="w-4 h-4" />
          </button>
          <button className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all">
            <Save className="w-4 h-4" />
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--primary)] text-white text-xs font-medium hover:bg-[var(--primary-hover)] transition-colors">
            <Download className="w-3.5 h-3.5" />
            导出
          </button>
        </div>
      </header>

      {/* 主体三栏 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧边栏 — 目录树 */}
        <AnimatePresence>
          {showSidebar && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 240, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="shrink-0 border-r border-[var(--border-subtle)] bg-[var(--bg-elevated)] overflow-hidden"
            >
              <div className="w-[240px] h-full flex flex-col">
                <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
                  <p className="text-xs text-[var(--text-tertiary)] font-medium flex items-center gap-1.5">
                    <FolderTree className="w-3.5 h-3.5" />
                    标书目录
                  </p>
                </div>
                <div className="flex-1 overflow-y-auto py-2">
                  {mockOutline.map((item) => (
                    <button
                      key={item.id}
                      className={`w-full text-left px-4 py-1.5 text-xs hover:bg-[var(--bg-surface)] transition-colors ${
                        item.depth === 0
                          ? "font-medium text-[var(--text-secondary)]"
                          : "text-[var(--text-tertiary)]"
                      }`}
                      style={{ paddingLeft: `${16 + item.depth * 16}px` }}
                    >
                      {item.title}
                    </button>
                  ))}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* 中间主编辑区 */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Step 进度条 */}
          <div className="shrink-0 px-6 py-3 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex items-center gap-1 max-w-2xl mx-auto">
              {STEPS.map((step, i) => (
                <div key={step.num} className="flex items-center flex-1">
                  <button
                    onClick={() => setCurrentStep(step.num)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                      currentStep === step.num
                        ? "bg-[var(--primary)] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]"
                        : currentStep > step.num
                        ? "bg-[rgba(34,197,94,0.1)] text-[var(--success)]"
                        : "text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)]"
                    }`}
                  >
                    {currentStep > step.num ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : (
                      <step.icon className="w-3.5 h-3.5" />
                    )}
                    {step.title}
                  </button>
                  {i < STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-px mx-1 ${
                        currentStep > step.num ? "bg-[var(--success)]" : "bg-[var(--border-subtle)]"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 内容区域 */}
          <div className="flex-1 overflow-y-auto p-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                transition={{ duration: 0.25 }}
              >
                {currentStep === 1 && <Step1Form />}
                {currentStep === 2 && <Step2Upload />}
                {currentStep >= 3 && <StepPlaceholder step={currentStep} />}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* 底部导航 */}
          <div className="shrink-0 px-6 py-3 border-t border-[var(--border-subtle)] bg-[var(--bg-elevated)] flex items-center justify-between">
            <button
              onClick={handlePrev}
              disabled={currentStep === 1}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[var(--border-default)] text-sm text-[var(--text-secondary)] hover:text-white hover:border-[var(--border-strong)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              上一步
            </button>
            <span className="text-xs text-[var(--text-tertiary)]">
              步骤 {currentStep} / 5
            </span>
            <button
              onClick={handleNext}
              disabled={currentStep === 5}
              className="btn-glow !px-5 !py-2 !text-sm !rounded-lg flex items-center gap-1.5 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              下一步
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </main>

        {/* 右侧 AI 面板 */}
        <AnimatePresence>
          {showChat && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 340, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="shrink-0 overflow-hidden"
            >
              <div className="w-[340px] h-full">
                <AIChatPanel onClose={() => setShowChat(false)} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* StatusBar */}
      <footer className="shrink-0 h-7 px-4 border-t border-[var(--border-subtle)] bg-[var(--bg-elevated)] flex items-center justify-between text-[10px] text-[var(--text-tertiary)]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
            AI 引擎就绪
          </span>
          <span>模型: DeepSeek-V3</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Token: 2,847 / 128K</span>
          <span>最后保存: 刚刚</span>
        </div>
      </footer>
    </div>
  );
}
