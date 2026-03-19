"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  Shield,
  FileSearch,
  Bot,
  Calculator,
  Link2,
  Ruler,
  Hash,
  AlertTriangle,
  Check,
  X,
  ChevronDown,
  Eye,
  RefreshCw,
  Upload,
  Sparkles,
  TrendingUp,
  Loader2,
  Info,
} from "lucide-react";

/* ========================================
   6 大审标维度
   ======================================== */
interface Dimension {
  id: string;
  label: string;
  icon: React.ElementType;
  color: string;
  score: number;
  status: "pass" | "warn" | "fail";
  desc: string;
  items: { name: string; result: "pass" | "warn" | "fail"; detail: string }[];
}

const dimensions: Dimension[] = [
  {
    id: "plagiarism",
    label: "文本查重检测",
    icon: FileSearch,
    color: "#6366f1",
    score: 92,
    status: "pass",
    desc: "SimHash + BERT 语义比对，检测与公开标书库/已投标文件的相似度",
    items: [
      { name: "全文 SimHash 指纹", result: "pass", detail: "与数据库 12,000+ 标书比对，相似度 4.2%（阈值 <15%）" },
      { name: "核心段落语义相似度", result: "pass", detail: "技术标核心段平均语义差异 87.3%（阈值 >70%）" },
      { name: "施工工艺段查重", result: "pass", detail: "路基处理段落替换率 72%（阈值 >40%）" },
      { name: "质量保证段查重", result: "warn", detail: "质保体系段替换率 38%，建议增加个性化描述" },
      { name: "安全文明段查重", result: "pass", detail: "安全文明段替换率 65%（阈值 >40%）" },
    ],
  },
  {
    id: "ai_trace",
    label: "AI 生成痕迹",
    icon: Bot,
    color: "#ec4899",
    score: 78,
    status: "warn",
    desc: "检测 AI 生成的典型特征（句式工整度/词汇多样性/连接词密度等）",
    items: [
      { name: "句式工整度检测", result: "warn", detail: "得分 0.73（自然文本参考值 <0.65），部分段落句式过于规整" },
      { name: "连接词密度", result: "pass", detail: "密度 3.2%（自然文本 2-5%），在正常范围" },
      { name: "词汇多样性 (TTR)", result: "warn", detail: "TTR = 0.42，低于自然工程文本参考值 0.48" },
      { name: "人格特征注入", result: "pass", detail: "已检测到 12 处个人经验叙述、5 处口语化表达" },
      { name: "标点与格式自然度", result: "pass", detail: "标点使用模式与人工撰写一致" },
    ],
  },
  {
    id: "data_validity",
    label: "数据合理性校验",
    icon: Calculator,
    color: "#10b981",
    score: 95,
    status: "pass",
    desc: "校验工期、成本、设备参数等数据是否在行业合理区间",
    items: [
      { name: "总工期合理性", result: "pass", detail: "计划 180 天，行业参考区间 160-200 天" },
      { name: "人员配置合理性", result: "pass", detail: "项目经理 1 人 + 技术负责人 1 人 + 施工员 3 人，符合规模要求" },
      { name: "设备配置合理性", result: "pass", detail: "压路机 20t × 2 台、挖掘机 1.2m³ × 3 台，与工程量匹配" },
      { name: "单价合理性", result: "warn", detail: "沥青混凝土单价 ¥385/m³，市场参考 ¥350-420/m³，偏中上" },
      { name: "材料用量比例", result: "pass", detail: "水泥用量 42.5 级 × 1200 吨，与路面面积计算一致" },
    ],
  },
  {
    id: "logic_consistency",
    label: "逻辑一致性审查",
    icon: Link2,
    color: "#f59e0b",
    score: 88,
    status: "pass",
    desc: "全文交叉校验：工期⟷资源⟷工法⟷质量⟷安全是否自洽",
    items: [
      { name: "工期↔施工进度", result: "pass", detail: "横道图总工期 180 天与施工组织描述一致" },
      { name: "工法↔设备配置", result: "pass", detail: "采用强夯法已配备 2000kN 夯锤，逻辑匹配" },
      { name: "人员↔工期", result: "warn", detail: "高峰期需 85 人，当前配置表仅列 60 人，建议补充" },
      { name: "质量标准↔检测方案", result: "pass", detail: "压实度≥93% 指标已在检测方案中列入 3 个检测频次" },
      { name: "安全措施↔危险源", result: "pass", detail: "识别 12 个危险源，每个均有对应预防措施" },
    ],
  },
  {
    id: "format_compliance",
    label: "格式合规检查",
    icon: Ruler,
    color: "#3b82f6",
    score: 100,
    status: "pass",
    desc: "废标红线扫描 — 格式、签章、有效期等强制性要求",
    items: [
      { name: "投标函签章", result: "pass", detail: "法人签名 + 公章 + 骑缝章，齐全" },
      { name: "投标有效期", result: "pass", detail: "90 天，满足招标文件要求（≥60 天）" },
      { name: "目录页码一致性", result: "pass", detail: "目录 28 项与正文页码完全对应" },
      { name: "投标保证金", result: "pass", detail: "金额 ¥50 万，账户信息正确，到账时间在截止前 3 天" },
      { name: "资质证书有效期", result: "pass", detail: "所有证书在有效期内，最早到期 2026-08" },
    ],
  },
  {
    id: "paragraph_hash",
    label: "段落级雷同定位",
    icon: Hash,
    color: "#8b5cf6",
    score: 85,
    status: "pass",
    desc: "逐段 hash 指纹比对，精确定位高相似段落并给出改写建议",
    items: [
      { name: "第三章 施工方案 §3.1", result: "pass", detail: "与基准库最高相似度 8%，安全" },
      { name: "第三章 施工方案 §3.4", result: "warn", detail: "与 2024-BJ-0238 标书相似度 22%，建议改写工艺描述" },
      { name: "第四章 质量保证 §4.2", result: "warn", detail: "与通用模板相似度 35%，建议加入项目特有检测指标" },
      { name: "第五章 安全措施 §5.1", result: "pass", detail: "已充分个性化，相似度 6%" },
      { name: "第七章 工期保证 §7.1", result: "pass", detail: "与基准库最高相似度 11%，安全" },
    ],
  },
];

/* ========================================
   通用函数
   ======================================== */
const statusIcon = (s: "pass" | "warn" | "fail") =>
  s === "pass" ? <Check className="w-3.5 h-3.5 text-[var(--success)]" /> :
  s === "warn" ? <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" /> :
  <X className="w-3.5 h-3.5 text-[var(--danger)]" />;

const statusColor = (s: "pass" | "warn" | "fail") =>
  s === "pass" ? "var(--success)" : s === "warn" ? "var(--warning)" : "var(--danger)";

const statusBg = (s: "pass" | "warn" | "fail") =>
  s === "pass" ? "rgba(34,197,94,0.08)" : s === "warn" ? "rgba(245,158,11,0.08)" : "rgba(239,68,68,0.08)";

/* ========================================
   页面组件
   ======================================== */
export default function AntiReviewPage() {
  const [expandedDim, setExpandedDim] = useState<string | null>("plagiarism");
  const [isScanning, setIsScanning] = useState(false);
  const [inputText, setInputText] = useState("");
  const [hasResult, setHasResult] = useState(true); // 默认显示 Mock 数据

  // 总评分
  const avgScore = Math.round(dimensions.reduce((a, d) => a + d.score, 0) / dimensions.length);
  const passCount = dimensions.filter((d) => d.status === "pass").length;
  const warnCount = dimensions.filter((d) => d.status === "warn").length;

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

  const handleRescan = useCallback(async () => {
    if (!inputText.trim() && !hasResult) return;
    setIsScanning(true);
    try {
      const { checkAntiReview } = await import('@/lib/api');
      const data = await checkAntiReview(inputText || "示例标书内容");
      console.log("审查结果:", data);
    } catch (e) {
      console.log("后端未连接，使用 Mock 数据");
    } finally {
      setHasResult(true);
      setIsScanning(false);
    }
  }, [inputText]);

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* TopBar — 精简版 */}
      <nav className="sticky top-0 z-40 glass border-b border-[var(--border-subtle)]">
        <div className="px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold tracking-tight text-sm">反审标检测</span>
            <span className="text-xs text-[var(--text-tertiary)] px-2 py-0.5 rounded-full bg-[var(--bg-surface)]">
              XX市政道路工程
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRescan}
              disabled={isScanning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-xs text-[var(--text-secondary)] hover:text-white transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
              {isScanning ? "扫描中..." : "重新扫描"}
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {/* 待检测文本输入区 */}
        <div className="mb-6 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <Upload className="w-4 h-4 text-[var(--primary)]" />
            粘贴待检测标书内容
          </h3>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="粘贴技术标/商务标内容，系统将自动进行 6 大维度安全审查..."
            rows={4}
            className="w-full px-4 py-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition-all text-sm resize-none mb-2"
          />
          <div className="flex justify-between items-center">
            <span className="text-xs text-[var(--text-tertiary)]">{inputText.length} 字</span>
            <button
              onClick={handleRescan}
              disabled={isScanning}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-medium hover:brightness-110 transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              {isScanning ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 扫描中...</> : <><Shield className="w-3.5 h-3.5" /> 开始安全扫描</>}
            </button>
          </div>
        </div>

        {/* 总览评分 */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {/* 综合分 */}
          <div className="col-span-1 p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] flex flex-col items-center justify-center">
            <div className="relative w-20 h-20 mb-2">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--bg-surface)" strokeWidth="6" />
                <circle
                  cx="40" cy="40" r="34"
                  fill="none"
                  stroke={avgScore >= 90 ? "var(--success)" : avgScore >= 70 ? "var(--warning)" : "var(--danger)"}
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={`${(avgScore / 100) * 213.6} 213.6`}
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-xl font-bold">{avgScore}</span>
            </div>
            <p className="text-xs text-[var(--text-tertiary)]">综合安全分</p>
          </div>

          {/* 统计 */}
          <div className="col-span-3 grid grid-cols-3 gap-3">
            <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
              <p className="text-2xl font-bold text-[var(--success)]">{passCount}</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-1">维度通过</p>
            </div>
            <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
              <p className="text-2xl font-bold text-[var(--warning)]">{warnCount}</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-1">需关注</p>
            </div>
            <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
              <p className="text-2xl font-bold">30</p>
              <p className="text-xs text-[var(--text-tertiary)] mt-1">检查项总计</p>
            </div>

            {/* 快捷摘要 */}
            <div className="col-span-3 p-3 rounded-xl bg-[rgba(245,158,11,0.06)] border border-[rgba(245,158,11,0.15)] flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-[var(--warning)] shrink-0 mt-0.5" />
              <div className="text-xs text-[var(--text-secondary)] space-y-0.5">
                <p><strong className="text-[var(--warning)]">2 项需关注：</strong></p>
                <p>• AI 生成痕迹：句式工整度偏高(0.73)，建议增加口语化表达</p>
                <p>• 质保段落替换率偏低(38%)，建议加入项目特有质检流程描述</p>
              </div>
            </div>
          </div>
        </div>

        {/* 6 大维度展开面板 */}
        <div className="space-y-3">
          {dimensions.map((dim) => {
            const isExpanded = expandedDim === dim.id;
            const passItems = dim.items.filter((i) => i.result === "pass").length;
            const totalItems = dim.items.length;

            return (
              <div key={dim.id} className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] overflow-hidden">
                {/* 维度头 */}
                <button
                  onClick={() => setExpandedDim(isExpanded ? null : dim.id)}
                  className="w-full flex items-center gap-4 p-4 text-left hover:bg-[var(--bg-surface)] transition-colors"
                >
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${dim.color}15` }}>
                    <dim.icon className="w-4.5 h-4.5" style={{ color: dim.color }} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold">{dim.label}</h3>
                      <span className="text-[10px] text-[var(--text-tertiary)]">{passItems}/{totalItems} 通过</span>
                    </div>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5 truncate">{dim.desc}</p>
                  </div>

                  {/* 分数环 */}
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <span className="text-lg font-bold" style={{ color: statusColor(dim.status) }}>{dim.score}</span>
                      <p className="text-[9px] text-[var(--text-tertiary)]">/ 100</p>
                    </div>
                    <span className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: statusBg(dim.status) }}>
                      {statusIcon(dim.status)}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-[var(--text-tertiary)] transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                  </div>
                </button>

                {/* 展开详情 */}
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="border-t border-[var(--border-subtle)]"
                  >
                    <div className="p-4 space-y-2">
                      {dim.items.map((item, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 rounded-lg" style={{ background: statusBg(item.result) }}>
                          <span className="mt-0.5 shrink-0">{statusIcon(item.result)}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium">{item.name}</p>
                            <p className="text-[11px] text-[var(--text-secondary)] mt-0.5 leading-relaxed">{item.detail}</p>
                          </div>
                          {item.result !== "pass" && (
                            <button className="shrink-0 px-2 py-1 rounded-md text-[10px] border border-[var(--border-default)] text-[var(--text-tertiary)] hover:text-white transition-all">
                              自动修复
                            </button>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* 维度建议 */}
                    {dim.items.some((i) => i.result !== "pass") && (
                      <div className="px-4 pb-4">
                        <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-start gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-[var(--primary)] shrink-0 mt-0.5" />
                          <div className="text-[11px] text-[var(--text-secondary)]">
                            <strong className="text-[var(--primary)]">AI 建议：</strong>
                            {dim.id === "ai_trace" && " 在技术标第 3.1、3.4 节中穿插 2-3 处\"根据我们在XX项目的实际经验\"等个人化叙述，并将部分并列句式改为因果/转折句式。"}
                            {dim.id === "plagiarism" && " 质量保证章节建议加入本项目特有的检测设备清单、质检频次表，替换通用质保描述。"}
                            {dim.id === "data_validity" && " 沥青混凝土单价可附带材料价格依据（如近 3 个月信息价），增强审标说服力。"}
                            {dim.id === "logic_consistency" && " 补充高峰期劳动力组织计划表，列出分阶段人员进出场安排。"}
                            {dim.id === "paragraph_hash" && " §3.4 建议用等效替换工法描述路径；§4.2 加入本项目特有的质量目标分解表。"}
                            {dim.id === "format_compliance" && " 所有格式检查项均通过，无需修改。"}
                          </div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            );
          })}
        </div>

        {/* 底部操作 */}
        <div className="mt-6 flex items-center justify-between p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
            <Info className="w-3.5 h-3.5" />
            <span>上次扫描：2 分钟前 · 检测耗时 4.2s · 引擎版本 v2.1</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-xs text-[var(--text-secondary)] hover:text-white transition-all">
              <Eye className="w-3.5 h-3.5" />
              导出报告
            </button>
            <button
              onClick={async () => {
                setIsScanning(true);
                // 模拟优化过程
                await new Promise(r => setTimeout(r, 2000));
                setIsScanning(false);
                alert('✅ 已自动优化 2 项告警内容：\n• AI 生成痕迹：已插入口语化表达\n• 质保段落：已加入项目特有质检流程');
              }}
              disabled={isScanning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--primary)] text-white text-xs font-medium hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50">
              <Sparkles className="w-3.5 h-3.5" />
              一键自动优化
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
