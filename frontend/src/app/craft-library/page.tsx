"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Sparkles,
  BookOpen,
  Search,
  Star,
  Award,
  AlertTriangle,
  BarChart3,
  FileText,
  Wrench,
  Building2,
  Route,
  Droplets,
  TreePine,
  Layers,
  GitBranch,
  Zap,
  TrendingUp,
  ArrowRight,
} from "lucide-react";

/* ========================================
   施工工艺知识树 — 市政 + 房建
   ======================================== */
interface CraftNode {
  id: string;
  label: string;
  icon?: React.ElementType;
  children?: CraftNode[];
  score?: number;
  docCount?: number;
}

const craftTree: CraftNode[] = [
  {
    id: "municipal",
    label: "市政工程",
    icon: Route,
    children: [
      {
        id: "road",
        label: "道路工程",
        children: [
          { id: "roadbed", label: "路基处理", docCount: 24, score: 92 },
          { id: "pavement", label: "路面结构", docCount: 18, score: 89 },
          { id: "drainage", label: "排水系统", docCount: 15, score: 87 },
          { id: "accessory", label: "附属设施", docCount: 9, score: 85 },
        ],
      },
      {
        id: "bridge",
        label: "桥梁工程",
        children: [
          { id: "substructure", label: "下部结构", docCount: 12, score: 91 },
          { id: "superstructure", label: "上部结构", docCount: 14, score: 90 },
        ],
      },
      {
        id: "pipeline",
        label: "管网工程",
        icon: Droplets,
        children: [
          { id: "water_supply", label: "给水管道", docCount: 11, score: 88 },
          { id: "sewage", label: "排水管道", docCount: 13, score: 86 },
        ],
      },
      {
        id: "landscape",
        label: "园林绿化",
        icon: TreePine,
        children: [
          { id: "terrain", label: "地形营造", docCount: 6, score: 84 },
          { id: "planting", label: "种植工程", docCount: 8, score: 83 },
        ],
      },
    ],
  },
  {
    id: "building",
    label: "房建工程",
    icon: Building2,
    children: [
      {
        id: "foundation",
        label: "基础工程",
        children: [
          { id: "pile", label: "桩基础", docCount: 16, score: 93 },
          { id: "raft", label: "筏板基础", docCount: 10, score: 90 },
        ],
      },
      {
        id: "structure",
        label: "主体结构",
        children: [
          { id: "frame", label: "框架结构", docCount: 20, score: 91 },
          { id: "shearwall", label: "剪力墙结构", docCount: 15, score: 92 },
          { id: "steel", label: "钢结构", docCount: 12, score: 89 },
          { id: "prefab", label: "装配式建筑", docCount: 8, score: 87 },
        ],
      },
      {
        id: "mep",
        label: "机电安装",
        children: [
          { id: "plumbing", label: "给排水", docCount: 14, score: 88 },
          { id: "hvac", label: "暖通空调", docCount: 11, score: 86 },
          { id: "electrical", label: "电气工程", docCount: 13, score: 87 },
          { id: "fire", label: "消防工程", docCount: 9, score: 90 },
        ],
      },
      {
        id: "decoration",
        label: "装饰装修",
        children: [
          { id: "plastering", label: "抹灰工程", docCount: 7, score: 84 },
          { id: "curtainwall", label: "幕墙工程", docCount: 10, score: 88 },
        ],
      },
    ],
  },
];

/* ========================================
   Mock 工艺节点详情
   ======================================== */
const mockCraftDetail = {
  id: "roadbed",
  title: "路基处理工艺",
  category: "市政工程 > 道路工程 > 路基处理",
  methods: [
    { name: "换填法", suitability: "软弱地基，深度≤3m", difficulty: "低", cost: "中" },
    { name: "强夯法", suitability: "杂填土/湿陷性黄土", difficulty: "中", cost: "低" },
    { name: "CFG桩复合地基", suitability: "深层软基，深度3-15m", difficulty: "高", cost: "高" },
    { name: "水泥搅拌桩", suitability: "淤泥质软土", difficulty: "中", cost: "中" },
    { name: "预压法", suitability: "大面积软基处理", difficulty: "低", cost: "低" },
  ],
  workflow: [
    "场地清表 → 测量放线",
    "原地面处理/清淤",
    "分层回填压实（每层≤30cm）",
    "压实度检测（≥93%）",
    "弯沉值检测验收",
  ],
  parameters: [
    { name: "压实度", standard: "≥93%（路床顶面≥96%）", source: "JTG F10-2006" },
    { name: "弯沉值", standard: "≤200（0.01mm）", source: "设计文件" },
    { name: "CBR 值", standard: "≥8%（上路床）", source: "JTG D30-2015" },
    { name: "填料最大粒径", standard: "≤100mm", source: "JTG F10-2006" },
  ],
  risks: [
    "路基不均匀沉降 — 控制措施：分层碾压+沉降观测",
    "边坡滑塌 — 控制措施：合理放坡+排水设施",
    "弹簧土 — 控制措施：翻挖晾晒+掺灰处理",
  ],
  highScoreParagraph: `本工程路基处理采用"换填+强夯"组合工艺。路基范围内先清除表土30cm，对软弱地基段（K2+100~K2+380）采用换填碎石垫层，厚度50cm，分两层压实，压实度不低于96%。对杂填土段（K3+200~K3+500）采用强夯法处理,夯击能2000kN·m,每点夯击8~10击,最后两击平均夯沉量不超过50mm。路基填筑采用水平分层法施工，每层松铺厚度不超过30cm，采用20t振动压路机碾压6~8遍，经压实度检测合格后方可进行上一层填筑。`,
};

/* ========================================
   树节点递归组件
   ======================================== */
function TreeNode({
  node,
  depth = 0,
  onSelect,
  selectedId,
}: {
  node: CraftNode;
  depth?: number;
  onSelect: (id: string) => void;
  selectedId: string;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = node.id === selectedId;
  const Icon = node.icon;

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) setExpanded(!expanded);
          else onSelect(node.id);
        }}
        className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg transition-all text-xs ${
          isSelected
            ? "bg-[var(--primary-glow)] text-[var(--primary)]"
            : "hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]"
        }`}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {hasChildren ? (
          <ChevronDown className={`w-3 h-3 shrink-0 transition-transform ${expanded ? "" : "-rotate-90"}`} />
        ) : (
          <div className="w-3 h-3 shrink-0" />
        )}
        {Icon && <Icon className="w-3.5 h-3.5 shrink-0" />}
        <span className="flex-1 truncate">{node.label}</span>
        {node.docCount && (
          <span className="text-[9px] text-[var(--text-tertiary)]">{node.docCount}</span>
        )}
        {node.score && (
          <span className="text-[9px] text-[var(--primary)] font-medium">{node.score}</span>
        )}
      </button>

      <AnimatePresence>
        {expanded && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            {node.children!.map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                depth={depth + 1}
                onSelect={onSelect}
                selectedId={selectedId}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ========================================
   主页面
   ======================================== */
export default function CraftLibraryPage() {
  const [selectedId, setSelectedId] = useState("roadbed");
  const [searchQuery, setSearchQuery] = useState("");
  const detail = mockCraftDetail; // 后续根据 selectedId 动态加载

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* TopBar */}
      <nav className="sticky top-0 z-40 glass border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => (window.location.href = "/dashboard")} className="text-[var(--text-tertiary)] hover:text-white transition-colors">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold tracking-tight">施工工艺图谱</span>
            </div>
            <span className="text-xs text-[var(--text-tertiary)] px-2 py-0.5 rounded-full bg-[var(--bg-surface)]">
              市政 + 房建
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-[var(--text-tertiary)]">共 248 个工艺节点</span>
            <span className="flex items-center gap-1 text-xs text-[var(--success)]">
              <TrendingUp className="w-3 h-3" />
              持续学习中
            </span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex gap-6 min-h-[calc(100vh-120px)]">
          {/* 左侧 — 工艺树 */}
          <div className="w-72 shrink-0">
            {/* 搜索 */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
              <input
                type="text"
                placeholder="搜索工艺..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all"
              />
            </div>

            <div className="card-gradient-border p-2 overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
              {craftTree.map((node) => (
                <TreeNode
                  key={node.id}
                  node={node}
                  onSelect={setSelectedId}
                  selectedId={selectedId}
                />
              ))}
            </div>
          </div>

          {/* 右侧 — 工艺详情 */}
          <div className="flex-1 space-y-5 overflow-y-auto">
            {/* 标题 */}
            <div>
              <p className="text-[10px] text-[var(--text-tertiary)] mb-1">{detail.category}</p>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <Wrench className="w-5 h-5 text-[var(--primary)]" />
                {detail.title}
              </h1>
            </div>

            {/* 可选工法对比 */}
            <div className="card-gradient-border p-5">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-[var(--primary)]" />
                可选施工工法 ({detail.methods.length} 种)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-subtle)]">
                      <th className="text-left py-2 font-medium text-[var(--text-tertiary)]">工法名称</th>
                      <th className="text-left py-2 font-medium text-[var(--text-tertiary)]">适用条件</th>
                      <th className="text-center py-2 font-medium text-[var(--text-tertiary)]">难度</th>
                      <th className="text-center py-2 font-medium text-[var(--text-tertiary)]">成本</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.methods.map((m, i) => (
                      <tr key={i} className="border-b border-[var(--border-subtle)] last:border-0">
                        <td className="py-2.5 font-medium text-white">{m.name}</td>
                        <td className="py-2.5 text-[var(--text-secondary)]">{m.suitability}</td>
                        <td className="py-2.5 text-center">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                            m.difficulty === "低" ? "bg-[rgba(34,197,94,0.1)] text-[var(--success)]" :
                            m.difficulty === "中" ? "bg-[rgba(245,158,11,0.1)] text-[var(--warning)]" :
                            "bg-[rgba(239,68,68,0.1)] text-[var(--danger)]"
                          }`}>{m.difficulty}</span>
                        </td>
                        <td className="py-2.5 text-center">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                            m.cost === "低" ? "bg-[rgba(34,197,94,0.1)] text-[var(--success)]" :
                            m.cost === "中" ? "bg-[rgba(245,158,11,0.1)] text-[var(--warning)]" :
                            "bg-[rgba(239,68,68,0.1)] text-[var(--danger)]"
                          }`}>{m.cost}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* 施工工序 */}
              <div className="card-gradient-border p-5">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[var(--primary)]" />
                  标准施工工序
                </h3>
                <div className="space-y-2">
                  {detail.workflow.map((step, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="w-5 h-5 rounded-full bg-[var(--primary)] text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 技术参数 */}
              <div className="card-gradient-border p-5">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-[var(--primary)]" />
                  关键技术参数
                </h3>
                <div className="space-y-2">
                  {detail.parameters.map((p, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--border-subtle)] last:border-0">
                      <div>
                        <p className="text-xs font-medium text-white">{p.name}</p>
                        <p className="text-[10px] text-[var(--text-tertiary)]">{p.source}</p>
                      </div>
                      <span className="text-xs text-[var(--primary)] font-medium bg-[var(--primary-glow)] px-2.5 py-1 rounded-lg">{p.standard}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 风险预警 */}
            <div className="card-gradient-border p-5">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />
                常见缺陷 & 防治
              </h3>
              <div className="space-y-2">
                {detail.risks.map((r, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                    <span className="text-[var(--warning)] mt-0.5">⚠</span>
                    <p>{r}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 高分范文段落 */}
            <div className="card-gradient-border p-5">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-400" />
                高分案例段落
                <span className="text-[10px] text-amber-400 bg-[rgba(251,191,36,0.1)] px-2 py-0.5 rounded-full ml-auto">
                  AI 评分 94.5
                </span>
              </h3>
              <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] leading-relaxed">
                {detail.highScoreParagraph}
              </div>
              <div className="flex items-center gap-2 mt-3">
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--primary)] text-white text-[10px] font-medium hover:bg-[var(--primary-hover)] transition-colors">
                  <Sparkles className="w-3 h-3" />
                  基于此段落生成变体
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-[10px] text-[var(--text-secondary)] hover:text-white transition-all">
                  <FileText className="w-3 h-3" />
                  引用到当前标书
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
