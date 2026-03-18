"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Shuffle,
  Shield,
  Eye,
  Download,
  Play,
  Pause,
  ChevronLeft,
  Check,
  AlertTriangle,
  XCircle,
  FileText,
  Layers,
  Paintbrush,
  LayoutGrid,
  Calculator,
  BookOpen,
  Palette,
  TrendingUp,
  Loader2,
  BarChart3,
  Zap,
} from "lucide-react";

/* ========================================
   变体维度定义
   ======================================== */
const VARIANT_DIMENSIONS = [
  {
    id: "craft",
    icon: Layers,
    label: "施工方案路线",
    desc: "3-5 种等效可行施工工法",
    options: ["明挖法", "顶管法", "盾构法", "沉管法"],
    selected: ["明挖法", "顶管法"],
  },
  {
    id: "style",
    icon: Paintbrush,
    label: "语言风格",
    desc: "不同的叙事口吻和行文风格",
    options: ["技术严谨型", "实战经验型", "学术引用型", "简洁务实型", "官方公文型"],
    selected: ["技术严谨型", "实战经验型", "简洁务实型"],
  },
  {
    id: "layout",
    icon: LayoutGrid,
    label: "排版结构",
    desc: "章节顺序/分节粒度/图表位置",
    options: ["工序先行型", "质量优先型", "安全突出型", "标准规范型"],
    selected: ["工序先行型", "质量优先型"],
  },
  {
    id: "params",
    icon: Calculator,
    label: "工期/参数浮动",
    desc: "合理区间内浮动设备参数和工期节点",
    options: ["±3%", "±5%", "±8%", "±10%"],
    selected: ["±5%"],
  },
  {
    id: "cases",
    icon: BookOpen,
    label: "引用案例轮换",
    desc: "从企业业绩库中轮换不同历史项目",
    options: ["2023年市政道路A项目", "2024年排水管网B项目", "2022年桥梁C项目", "2024年房建D项目"],
    selected: ["2023年市政道路A项目", "2024年排水管网B项目"],
  },
  {
    id: "format",
    icon: Palette,
    label: "排版样式",
    desc: "6+ 种文档视觉样式模板",
    options: ["传统稳重", "现代简约", "图文丰富", "数据驱动", "极简留白", "工程蓝图"],
    selected: ["传统稳重", "现代简约"],
  },
];

/* ========================================
   Mock 变体列表
   ======================================== */
const mockVariants = [
  { id: 1, name: "变体 A-01", style: "技术严谨+明挖法+传统稳重", similarity: 12, score: 91.2, status: "done" },
  { id: 2, name: "变体 A-02", style: "实战经验+顶管法+现代简约", similarity: 8, score: 89.7, status: "done" },
  { id: 3, name: "变体 A-03", style: "简洁务实+明挖法+图文丰富", similarity: 15, score: 88.3, status: "done" },
  { id: 4, name: "变体 B-01", style: "技术严谨+盾构法+数据驱动", similarity: 6, score: 93.1, status: "done" },
  { id: 5, name: "变体 B-02", style: "学术引用+顶管法+极简留白", similarity: 11, score: 87.9, status: "generating" },
  { id: 6, name: "变体 C-01", style: "官方公文+明挖法+工程蓝图", similarity: 9, score: null, status: "pending" },
];

/* ========================================
   页面组件
   ======================================== */
export default function VariantsPage() {
  const [targetCount, setTargetCount] = useState(10);
  const [isGenerating, setIsGenerating] = useState(false);
  const [expandedDim, setExpandedDim] = useState<string | null>("craft");

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => setIsGenerating(false), 5000);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* TopBar — 精简版 */}
      <nav className="sticky top-0 z-40 glass border-b border-[var(--border-subtle)]">
        <div className="px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
              <Shuffle className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold tracking-tight text-sm">变体生成引擎</span>
            <span className="text-xs text-[var(--text-tertiary)] px-2 py-0.5 rounded-full bg-[var(--bg-surface)]">
              XX市政道路工程
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-[var(--text-tertiary)]">已生成 4/10 份</span>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--primary)] text-white text-xs font-medium hover:bg-[var(--primary-hover)] transition-colors">
              <Download className="w-3.5 h-3.5" />
              批量导出
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧 — 变体维度控制 */}
          <div className="lg:col-span-1 space-y-4">
            <div className="card-gradient-border p-5">
              <h2 className="text-sm font-semibold mb-1 flex items-center gap-2">
                <Zap className="w-4 h-4 text-[var(--primary)]" />
                变体维度配置
              </h2>
              <p className="text-xs text-[var(--text-tertiary)] mb-4">
                选择变化维度和参数，AI 将排列组合生成不同变体
              </p>

              <div className="space-y-2">
                {VARIANT_DIMENSIONS.map((dim) => (
                  <div key={dim.id} className="rounded-xl border border-[var(--border-subtle)] overflow-hidden">
                    <button
                      onClick={() => setExpandedDim(expandedDim === dim.id ? null : dim.id)}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[var(--bg-surface)] transition-colors"
                    >
                      <dim.icon className="w-4 h-4 text-[var(--primary)] shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium">{dim.label}</p>
                        <p className="text-[10px] text-[var(--text-tertiary)] truncate">{dim.desc}</p>
                      </div>
                      <span className="text-[10px] text-[var(--primary)] bg-[var(--primary-glow)] px-1.5 py-0.5 rounded-full">{dim.selected.length}</span>
                    </button>

                    <AnimatePresence>
                      {expandedDim === dim.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="px-4 pb-3"
                        >
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {dim.options.map((opt) => (
                              <span
                                key={opt}
                                className={`px-2.5 py-1 rounded-full text-[10px] cursor-pointer transition-all ${
                                  dim.selected.includes(opt)
                                    ? "bg-[var(--primary)] text-white"
                                    : "bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-white border border-[var(--border-subtle)]"
                                }`}
                              >
                                {opt}
                              </span>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>
            </div>

            {/* 生成数量控制 */}
            <div className="card-gradient-border p-5">
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                目标生成数量
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={5}
                  max={100}
                  step={5}
                  value={targetCount}
                  onChange={(e) => setTargetCount(Number(e.target.value))}
                  className="flex-1 accent-[var(--primary)]"
                />
                <span className="text-2xl font-bold text-[var(--primary)] min-w-[3ch] text-right">{targetCount}</span>
              </div>
              <p className="text-[10px] text-[var(--text-tertiary)] mt-1">
                理论可生成组合数：{VARIANT_DIMENSIONS.reduce((acc, d) => acc * d.selected.length, 1)}+
              </p>

              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="btn-glow !w-full !py-3 !rounded-lg !text-sm mt-4 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> 生成中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" /> 开始批量生成
                  </>
                )}
              </button>
            </div>

            {/* 反查重指标 */}
            <div className="card-gradient-border p-5">
              <h3 className="text-xs font-semibold mb-3 flex items-center gap-2">
                <Shield className="w-3.5 h-3.5 text-[var(--success)]" />
                反查重指标
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-[var(--text-tertiary)]">平均语义差异度</span>
                    <span className="text-[var(--success)] font-medium">88.2%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-[var(--bg-surface)]">
                    <div className="h-full rounded-full bg-[var(--success)]" style={{ width: "88%" }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-[var(--text-tertiary)]">关键段落替换率</span>
                    <span className="text-[var(--success)] font-medium">67.5%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-[var(--bg-surface)]">
                    <div className="h-full rounded-full bg-[var(--success)]" style={{ width: "67%" }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-[var(--text-tertiary)]">AI 生成痕迹指数</span>
                    <span className="text-[var(--warning)] font-medium">23%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-[var(--bg-surface)]">
                    <div className="h-full rounded-full bg-[var(--warning)]" style={{ width: "23%" }} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧 — 变体列表 */}
          <div className="lg:col-span-2 space-y-4">
            {/* 统计横条 */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "已生成", value: "4", color: "var(--success)" },
                { label: "生成中", value: "1", color: "var(--primary)" },
                { label: "待生成", value: "5", color: "var(--text-tertiary)" },
                { label: "平均评分", value: "90.1", color: "var(--primary)" },
              ].map((s, i) => (
                <div key={i} className="p-3 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-center">
                  <p className="text-lg font-bold" style={{ color: s.color }}>{s.value}</p>
                  <p className="text-[10px] text-[var(--text-tertiary)]">{s.label}</p>
                </div>
              ))}
            </div>

            {/* 变体卡片列表 */}
            <div className="space-y-3">
              {mockVariants.map((v) => (
                <motion.div
                  key={v.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="group flex items-center gap-4 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)] transition-all"
                >
                  {/* 序号 */}
                  <div className="w-10 h-10 rounded-lg bg-[var(--primary-glow)] flex items-center justify-center shrink-0">
                    <span className="text-sm font-bold text-[var(--primary)]">{String(v.id).padStart(2, "0")}</span>
                  </div>

                  {/* 信息 */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold">{v.name}</h3>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5 truncate">{v.style}</p>
                  </div>

                  {/* 相似度 */}
                  <div className="text-center px-3">
                    <p className="text-xs font-bold" style={{
                      color: v.similarity < 10 ? "var(--success)" : v.similarity < 20 ? "var(--warning)" : "var(--danger)"
                    }}>
                      {v.similarity}%
                    </p>
                    <p className="text-[9px] text-[var(--text-tertiary)]">相似度</p>
                  </div>

                  {/* AI 评分 */}
                  <div className="text-center px-3">
                    {v.score !== null ? (
                      <>
                        <p className="text-xs font-bold text-[var(--primary)]">{v.score}</p>
                        <p className="text-[9px] text-[var(--text-tertiary)]">AI 评分</p>
                      </>
                    ) : (
                      <span className="text-[10px] text-[var(--text-tertiary)]">—</span>
                    )}
                  </div>

                  {/* 状态 */}
                  <div className="flex items-center gap-2">
                    {v.status === "done" && (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-[rgba(34,197,94,0.1)] text-[var(--success)]">
                        <Check className="w-2.5 h-2.5" /> 完成
                      </span>
                    )}
                    {v.status === "generating" && (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-[rgba(99,102,241,0.1)] text-[var(--primary)]">
                        <Loader2 className="w-2.5 h-2.5 animate-spin" /> 生成中
                      </span>
                    )}
                    {v.status === "pending" && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] bg-[var(--bg-surface)] text-[var(--text-tertiary)]">
                        待生成
                      </span>
                    )}

                    {v.status === "done" && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-1.5 rounded-md hover:bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-white transition-all">
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button className="p-1.5 rounded-md hover:bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-white transition-all">
                          <Download className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* 相似度热力图 */}
            <div className="card-gradient-border p-5">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-[var(--primary)]" />
                变体间相似度矩阵
              </h3>
              <div className="overflow-x-auto">
                <div className="inline-grid gap-1" style={{ gridTemplateColumns: `32px repeat(4, 48px)` }}>
                  {/* 表头 */}
                  <div />
                  {["A-01", "A-02", "A-03", "B-01"].map((h) => (
                    <div key={h} className="text-[9px] text-center text-[var(--text-tertiary)] py-1">{h}</div>
                  ))}

                  {/* 行数据 */}
                  {[
                    { label: "A-01", values: [0, 12, 15, 8] },
                    { label: "A-02", values: [12, 0, 18, 6] },
                    { label: "A-03", values: [15, 18, 0, 11] },
                    { label: "B-01", values: [8, 6, 11, 0] },
                  ].map((row) => (
                    <>
                      <div key={`label-${row.label}`} className="text-[9px] text-[var(--text-tertiary)] flex items-center">{row.label}</div>
                      {row.values.map((val, j) => (
                        <div
                          key={`${row.label}-${j}`}
                          className="w-12 h-8 rounded-md flex items-center justify-center text-[10px] font-medium"
                          style={{
                            background: val === 0
                              ? "var(--bg-surface)"
                              : `rgba(34, 197, 94, ${Math.max(0.08, 1 - val / 30)})`,
                            color: val === 0 ? "var(--text-tertiary)" : val < 15 ? "var(--success)" : "var(--warning)",
                          }}
                        >
                          {val === 0 ? "—" : `${val}%`}
                        </div>
                      ))}
                    </>
                  ))}
                </div>
              </div>
              <p className="text-[10px] text-[var(--text-tertiary)] mt-3">
                ✅ 所有变体对相似度均低于 20% 阈值，通过反查重校验
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
