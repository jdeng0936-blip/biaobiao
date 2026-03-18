"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import {
  Shield,
  Zap,
  Brain,
  FileSearch,
  BarChart3,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileText,
  Bot,
  Lock,
  Target,
  TrendingUp,
  Clock,
  Award,
} from "lucide-react";

/* ========================================
   动画工具
   ======================================== */
const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.4, 0, 0.2, 1] as const } },
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

/* ========================================
   Section 组件
   ======================================== */
function AnimatedSection({ children, className = "", id }: { children: React.ReactNode; className?: string; id?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  return (
    <motion.section
      ref={ref}
      id={id}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={staggerContainer}
      className={className}
    >
      {children}
    </motion.section>
  );
}

/* ========================================
   NavBar
   ======================================== */
function Navbar() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50 glass"
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight">标标 AI</span>
        </div>

        {/* 导航链接 */}
        <div className="hidden md:flex items-center gap-8 text-sm text-[var(--text-secondary)]">
          <a href="#features" className="hover:text-white transition-colors">核心能力</a>
          <a href="#workflow" className="hover:text-white transition-colors">工作流程</a>
          <a href="#stats" className="hover:text-white transition-colors">效能革命</a>
          <a href="#pricing" className="hover:text-white transition-colors">定价</a>
        </div>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <button className="text-sm text-[var(--text-secondary)] hover:text-white transition-colors px-4 py-2">
            登录
          </button>
          <button className="btn-glow !px-5 !py-2 !text-sm !rounded-lg">
            免费试用
          </button>
        </div>
      </div>
    </motion.nav>
  );
}

/* ========================================
   Hero Section
   ======================================== */
function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center hero-grid overflow-hidden pt-16">
      {/* 背景光效 */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[600px] rounded-full bg-[var(--primary)] opacity-[0.07] blur-[120px] animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-[var(--accent-violet)] opacity-[0.05] blur-[100px] animate-pulse-glow" style={{ animationDelay: "1.5s" }} />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* 标签 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[var(--border-default)] bg-[var(--bg-elevated)] mb-8 text-sm text-[var(--text-secondary)]"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
          全链路 AI 标书解决方案 · 建筑行业专属
        </motion.div>

        {/* 主标题 */}
        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6"
        >
          <span className="text-gradient">AI 驱动</span>
          <br />
          <span className="text-white">标书效能革命</span>
        </motion.h1>

        {/* 副标题 */}
        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.35 }}
          className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          从招标文件智能解读、多 Agent 并行撰写、模拟 AI 阅标评分，
          到像素级排版导出 —— <strong className="text-white">用 AI 对抗 AI</strong>，
          让每一份标书都精准命中评分点。
        </motion.p>

        {/* CTA 按钮组 */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <button className="btn-glow !px-8 !py-3.5 !text-base flex items-center gap-2 !rounded-xl">
            <Sparkles className="w-5 h-5" />
            立即开始制作
            <ArrowRight className="w-4 h-4" />
          </button>
          <button className="px-8 py-3.5 rounded-xl border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-white hover:border-[var(--border-strong)] transition-all text-base flex items-center gap-2">
            <FileText className="w-5 h-5" />
            查看演示
          </button>
        </motion.div>

        {/* 信任指标 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.7 }}
          className="mt-16 flex flex-wrap items-center justify-center gap-8 text-sm text-[var(--text-tertiary)]"
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
            数据本地脱敏 · G 端合规
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
            废标率降至 0.1%
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
            2 小时快速出稿
          </div>
        </motion.div>
      </div>

      {/* 底部渐变遮罩 */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[var(--bg-base)] to-transparent" />
    </section>
  );
}

/* ========================================
   痛点区块
   ======================================== */
const painPoints = [
  {
    icon: Target,
    title: "废标风险高悬",
    desc: "人工编制疲劳状态下极易遗漏「实质性响应条款」，电子阅标系统毫不留情地触发废标拦截。",
    color: "var(--danger)",
  },
  {
    icon: FileSearch,
    title: "同质化困境",
    desc: "模板套用千篇一律，AI 评标系统严查「技术方案雷同度」，套路化文本难获高分。",
    color: "var(--warning)",
  },
  {
    icon: Clock,
    title: "效率极限",
    desc: "3-4 人团队封闭 7-14 天，70% 时间消耗在翻找资料和交叉校对上。",
    color: "var(--accent-blue)",
  },
];

function PainPointsSection() {
  return (
    <AnimatedSection className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.div variants={fadeInUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-[var(--primary)] tracking-widest uppercase mb-3">行业痛点</p>
          <h2 className="text-3xl md:text-4xl font-bold">
            传统标书模式的
            <span className="text-gradient"> 系统性崩溃</span>
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
          {painPoints.map((item, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              className="card-gradient-border p-8 hover:bg-[var(--bg-surface)] transition-colors duration-300 group"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-5"
                style={{ background: `${item.color}15` }}
              >
                <item.icon className="w-6 h-6" style={{ color: item.color }} />
              </div>
              <h3 className="text-xl font-semibold mb-3">{item.title}</h3>
              <p className="text-[var(--text-secondary)] leading-relaxed text-[15px]">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </AnimatedSection>
  );
}

/* ========================================
   核心能力 Features
   ======================================== */
const features = [
  {
    icon: FileSearch,
    title: "智能文件解读",
    desc: "VLM 多模态解析引擎，精准提取废标红线、评分标准、结构化大纲，复杂表格零偏差。",
  },
  {
    icon: Brain,
    title: "Multi-Agent 协作撰写",
    desc: "多个 AI Agent 并行撰写不同章节，全局审阅模型统一语言风格，消除逻辑矛盾。",
  },
  {
    icon: Shield,
    title: "模拟 AI 阅标评分",
    desc: "内置审查智能体，以电子评标系统视角扫描全文，在定稿前拦截一切废标隐患。",
  },
  {
    icon: Lock,
    title: "混合安全架构",
    desc: "本地模型脱敏处理敏感数据，云端模型负责复杂推理。PII 信息绝不外泄。",
  },
  {
    icon: Zap,
    title: "高熵防撞车引擎",
    desc: "融入项目特有环境变量动态重写，确保每次生成文本唯一，通过严格查重审查。",
  },
  {
    icon: BarChart3,
    title: "像素级排版导出",
    desc: "自动对齐行业标准：目录序号递进、字号行距、段落缩进，一键导出 Word/PDF。",
  },
];

function FeaturesSection() {
  return (
    <AnimatedSection className="py-24 px-6" id="features">
      <div className="max-w-6xl mx-auto">
        <motion.div variants={fadeInUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-[var(--primary)] tracking-widest uppercase mb-3">核心能力</p>
          <h2 className="text-3xl md:text-4xl font-bold">
            六大 AI 引擎，
            <span className="text-gradient">全链路赋能</span>
          </h2>
          <p className="mt-4 text-[var(--text-secondary)] max-w-xl mx-auto">
            不止于生成文本 — 从解读、撰写、审查到导出，每一步都有专属 AI 引擎深度介入。
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((item, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              className="group relative p-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)] transition-all duration-300"
            >
              <div className="w-11 h-11 rounded-lg bg-[var(--primary-glow)] flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                <item.icon className="w-5 h-5 text-[var(--primary)]" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
              <p className="text-[var(--text-secondary)] text-[14.5px] leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </AnimatedSection>
  );
}

/* ========================================
   工作流程 Workflow
   ======================================== */
const steps = [
  { num: "01", title: "标书设置", desc: "选择标书类型、工程类别，配置基本参数", icon: FileText },
  { num: "02", title: "招标文件解读", desc: "AI 自动解析文件，提取废标红线与评分标准", icon: FileSearch },
  { num: "03", title: "AI 目录生成", desc: "基于解读结果自动生成标书目录，支持拖拽", icon: Bot },
  { num: "04", title: "内容生成", desc: "Multi-Agent 并行撰写，实时流式输出", icon: Brain },
  { num: "05", title: "审查与导出", desc: "模拟阅标评分 + 查重 + 一键导出 Word/PDF", icon: Shield },
];

function WorkflowSection() {
  return (
    <AnimatedSection className="py-24 px-6" id="workflow">
      <div className="max-w-5xl mx-auto">
        <motion.div variants={fadeInUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-[var(--primary)] tracking-widest uppercase mb-3">工作流程</p>
          <h2 className="text-3xl md:text-4xl font-bold">
            五步完成
            <span className="text-gradient"> 高分标书</span>
          </h2>
        </motion.div>

        <div className="relative">
          {/* 连接线 */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--primary)] to-transparent opacity-20 -translate-y-1/2" />

          <div className="grid lg:grid-cols-5 gap-6 lg:gap-4">
            {steps.map((step, i) => (
              <motion.div key={i} variants={fadeInUp} className="relative text-center group">
                <div className="relative z-10 mx-auto w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center mb-4 group-hover:border-[var(--primary)] group-hover:shadow-[0_0_24px_rgba(99,102,241,0.15)] transition-all duration-300">
                  <step.icon className="w-6 h-6 text-[var(--primary)]" />
                </div>
                <p className="text-xs text-[var(--primary)] font-mono font-bold mb-1">{step.num}</p>
                <h3 className="text-base font-semibold mb-1">{step.title}</h3>
                <p className="text-xs text-[var(--text-tertiary)] leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </AnimatedSection>
  );
}

/* ========================================
   数据背书 Stats
   ======================================== */
const stats = [
  { value: "500%+", label: "效率提升", icon: TrendingUp },
  { value: "0.1%", label: "废标率", icon: Shield },
  { value: "2h", label: "平均出稿", icon: Clock },
  { value: "150万/年", label: "人力成本节省", icon: Award },
];

function StatsSection() {
  return (
    <AnimatedSection className="py-24 px-6" id="stats">
      <div className="max-w-6xl mx-auto">
        <motion.div variants={fadeInUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-[var(--primary)] tracking-widest uppercase mb-3">效能革命</p>
          <h2 className="text-3xl md:text-4xl font-bold">
            从 <span className="text-gradient">&ldquo;周/天&rdquo;</span> 到 <span className="text-gradient">&ldquo;小时&rdquo;</span> 的跨越
          </h2>
        </motion.div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((item, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              className="card-gradient-border p-8 text-center group"
            >
              <div className="w-12 h-12 rounded-xl mx-auto mb-4 bg-[var(--primary-glow)] flex items-center justify-center group-hover:scale-110 transition-transform">
                <item.icon className="w-6 h-6 text-[var(--primary)]" />
              </div>
              <p className="text-3xl md:text-4xl font-extrabold text-gradient mb-2">{item.value}</p>
              <p className="text-[var(--text-secondary)] text-sm">{item.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </AnimatedSection>
  );
}

/* ========================================
   定价方案 Pricing
   ======================================== */
const plans = [
  {
    name: "入门版",
    price: "免费",
    period: "",
    desc: "适合个人投标专员体验",
    features: ["每月 3 份标书解析", "基础 AI 内容生成", "标准模板库", "Word 导出"],
    cta: "免费开始",
    highlighted: false,
  },
  {
    name: "专业版",
    price: "¥1,999",
    period: "/月",
    desc: "适合中小型建筑施工企业",
    features: [
      "无限标书项目",
      "所有 AI 引擎全开放",
      "企业知识库 (10GB)",
      "模拟阅标评分",
      "防撞车查重",
      "优先客户支持",
    ],
    cta: "立即升级",
    highlighted: true,
  },
  {
    name: "企业版",
    price: "定制",
    period: "",
    desc: "适合大型国企/集团私有化部署",
    features: [
      "本地化部署 + 云端混合",
      "数据完全私有化",
      "专属模型微调",
      "无限知识库容量",
      "API 接入",
      "7×24 专属技术支持",
    ],
    cta: "联系我们",
    highlighted: false,
  },
];

function PricingSection() {
  return (
    <AnimatedSection className="py-24 px-6" id="pricing">
      <div className="max-w-6xl mx-auto">
        <motion.div variants={fadeInUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-[var(--primary)] tracking-widest uppercase mb-3">定价方案</p>
          <h2 className="text-3xl md:text-4xl font-bold">
            选择适合您的
            <span className="text-gradient"> 投标方案</span>
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6 items-stretch">
          {plans.map((plan, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              className={`relative rounded-2xl p-8 flex flex-col ${
                plan.highlighted
                  ? "card-gradient-border bg-[var(--bg-elevated)] shadow-[0_0_48px_rgba(99,102,241,0.08)]"
                  : "border border-[var(--border-subtle)] bg-[var(--bg-elevated)]"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent-violet)] text-xs font-semibold text-white">
                  最受欢迎
                </div>
              )}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-1">{plan.name}</h3>
                <p className="text-sm text-[var(--text-tertiary)]">{plan.desc}</p>
              </div>
              <div className="mb-6">
                <span className="text-4xl font-extrabold">{plan.price}</span>
                <span className="text-[var(--text-tertiary)] text-sm">{plan.period}</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature, j) => (
                  <li key={j} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                    <CheckCircle2 className="w-4 h-4 text-[var(--success)] mt-0.5 shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <button
                className={`w-full py-3 rounded-xl text-sm font-semibold transition-all ${
                  plan.highlighted
                    ? "btn-glow !w-full !rounded-xl"
                    : "border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-white hover:border-[var(--border-strong)]"
                }`}
              >
                {plan.cta}
                <ChevronRight className="w-4 h-4 inline ml-1" />
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </AnimatedSection>
  );
}

/* ========================================
   CTA Section
   ======================================== */
function CTASection() {
  return (
    <AnimatedSection className="py-24 px-6">
      <motion.div
        variants={fadeInUp}
        className="max-w-4xl mx-auto text-center relative rounded-3xl overflow-hidden p-16"
      >
        {/* 背景 */}
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)] via-[var(--accent-violet)] to-[var(--accent-purple)] opacity-10 animate-gradient" />
        <div className="absolute inset-0 border border-[var(--border-subtle)] rounded-3xl" />

        <div className="relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            准备好让 AI 重新定义<br />你的投标效率了吗？
          </h2>
          <p className="text-[var(--text-secondary)] mb-8 max-w-lg mx-auto">
            从今天开始，告别通宵赶标书的噩梦。让 AI 成为你最强大的投标武器。
          </p>
          <button className="btn-glow !px-10 !py-4 !text-base !rounded-xl flex items-center gap-2 mx-auto">
            <Sparkles className="w-5 h-5" />
            免费试用 · 无需信用卡
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    </AnimatedSection>
  );
}

/* ========================================
   Footer
   ======================================== */
function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-[var(--border-subtle)]">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-4 gap-8 mb-12">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold">标标 AI</span>
            </div>
            <p className="text-sm text-[var(--text-tertiary)] leading-relaxed">
              全程 AI 赋能的标书制作平台，<br />专为建筑行业打造。
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-sm mb-4">产品</h4>
            <ul className="space-y-2 text-sm text-[var(--text-tertiary)]">
              <li><a href="#" className="hover:text-white transition-colors">AI 标书写作</a></li>
              <li><a href="#" className="hover:text-white transition-colors">招标文件解读</a></li>
              <li><a href="#" className="hover:text-white transition-colors">模拟阅标评分</a></li>
              <li><a href="#" className="hover:text-white transition-colors">知识库管理</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sm mb-4">资源</h4>
            <ul className="space-y-2 text-sm text-[var(--text-tertiary)]">
              <li><a href="#" className="hover:text-white transition-colors">产品文档</a></li>
              <li><a href="#" className="hover:text-white transition-colors">API 接口</a></li>
              <li><a href="#" className="hover:text-white transition-colors">使用教程</a></li>
              <li><a href="#" className="hover:text-white transition-colors">博客</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sm mb-4">公司</h4>
            <ul className="space-y-2 text-sm text-[var(--text-tertiary)]">
              <li><a href="#" className="hover:text-white transition-colors">关于我们</a></li>
              <li><a href="#" className="hover:text-white transition-colors">联系我们</a></li>
              <li><a href="#" className="hover:text-white transition-colors">隐私政策</a></li>
              <li><a href="#" className="hover:text-white transition-colors">服务条款</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-[var(--border-subtle)] flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-[var(--text-tertiary)]">
            © 2026 标标 AI. All rights reserved.
          </p>
          <p className="text-xs text-[var(--text-tertiary)]">
            沪ICP备XXXXXXXX号-1 · 沪公网安备XXXXXXXXXXXXX号
          </p>
        </div>
      </div>
    </footer>
  );
}

/* ========================================
   页面组装
   ======================================== */
export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <HeroSection />
      <PainPointsSection />
      <FeaturesSection />
      <WorkflowSection />
      <StatsSection />
      <PricingSection />
      <CTASection />
      <Footer />
    </main>
  );
}
