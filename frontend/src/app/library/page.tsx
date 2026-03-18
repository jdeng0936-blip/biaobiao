"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  Search,
  Briefcase,
  BookOpen,
  Scale,
  ShieldCheck,
  Image,
  FolderTree,
  FileText,
  Upload,
  Star,
  Clock,
  Filter,
  Grid3x3,
  List,
  Lock,
  Eye,
  Plus,
  ChevronRight,
  TrendingUp,
  Building2,
  Wrench,
  Sparkles,
} from "lucide-react";
import PaywallModal from "@/components/shared/PaywallModal";

/* ========================================
   6 大资料库分类
   ======================================== */
const LIBRARY_TABS = [
  { id: "business", label: "商务资料库", icon: Briefcase, color: "#6366f1", count: 1240, desc: "营业执照/资质证书/业绩/人员" },
  { id: "knowledge", label: "知识库", icon: BookOpen, color: "#3b82f6", count: 860, desc: "行业知识/方案模板/经验积累" },
  { id: "standards", label: "规范库", icon: Scale, color: "#10b981", count: 2100, desc: "国标/行标/地标/技术规程" },
  { id: "barriers", label: "技术壁垒库", icon: ShieldCheck, color: "#f59e0b", count: 380, desc: "废标红线/评审陷阱/得分秘籍" },
  { id: "images", label: "图片库", icon: Image, color: "#ec4899", count: 5600, desc: "施工图/平面图/效果图/工艺图" },
  { id: "craft", label: "施工工艺库", icon: Wrench, color: "#14b8a6", count: 248, desc: "市政+房建完整工艺图谱" },
];

/* ========================================
   Mock 资料数据
   ======================================== */
const mockItems: Record<string, Array<{ id: string; title: string; tags: string[]; date: string; premium: boolean }>> = {
  business: [
    { id: "1", title: "企业营业执照模板", tags: ["资质", "通用"], date: "2024-01", premium: false },
    { id: "2", title: "市政公用工程施工总承包一级", tags: ["资质证书"], date: "2024-03", premium: false },
    { id: "3", title: "类似工程业绩汇总表", tags: ["业绩", "模板"], date: "2024-02", premium: false },
    { id: "4", title: "项目经理履历及业绩证明", tags: ["人员", "模板"], date: "2024-01", premium: false },
    { id: "5", title: "投标保函/保证金模板", tags: ["商务", "财务"], date: "2023-12", premium: false },
    { id: "6", title: "联合体协议范本", tags: ["商务"], date: "2024-03", premium: true },
  ],
  knowledge: [
    { id: "k1", title: "技术标编写通用框架", tags: ["技术标", "框架"], date: "2024-03", premium: false },
    { id: "k2", title: "施工组织设计编写要点", tags: ["施组", "技巧"], date: "2024-02", premium: false },
    { id: "k3", title: "工期进度计划横道图绘制指南", tags: ["工期", "图表"], date: "2024-01", premium: false },
    { id: "k4", title: "质量保证体系模板（ISO 9001）", tags: ["质量", "体系"], date: "2024-03", premium: true },
    { id: "k5", title: "安全文明施工方案范本", tags: ["安全", "范本"], date: "2024-02", premium: false },
    { id: "k6", title: "环境保护与绿色施工措施", tags: ["环保"], date: "2024-01", premium: true },
  ],
  standards: [
    { id: "s1", title: "JTG F10-2006 公路路基施工技术规范", tags: ["路基", "国标"], date: "2006", premium: false },
    { id: "s2", title: "JTG D30-2015 公路路基设计规范", tags: ["路基", "国标"], date: "2015", premium: false },
    { id: "s3", title: "GB 50500-2013 建设工程工程量清单计价规范", tags: ["计价", "国标"], date: "2013", premium: false },
    { id: "s4", title: "GB 50300-2013 建筑工程施工质量验收统一标准", tags: ["质量", "国标"], date: "2013", premium: false },
    { id: "s5", title: "CJJ 1-2008 城镇道路工程施工与质量验收规范", tags: ["市政", "行标"], date: "2008", premium: true },
    { id: "s6", title: "GB 50854-2013 房屋建筑与装饰工程工程量计算规范", tags: ["房建", "国标"], date: "2013", premium: true },
  ],
  barriers: [
    { id: "b1", title: "投标保证金未到账 → 废标", tags: ["废标", "红线"], date: "2024-03", premium: false },
    { id: "b2", title: "项目经理资质不符 → 废标", tags: ["废标", "人员"], date: "2024-03", premium: false },
    { id: "b3", title: "投标有效期不满足 → 废标", tags: ["废标", "时间"], date: "2024-02", premium: false },
    { id: "b4", title: "技术标评分加分项拆解（60 分制）", tags: ["得分", "技巧"], date: "2024-03", premium: true },
    { id: "b5", title: "AI 审标系统常见检测规则一览", tags: ["反审标"], date: "2024-03", premium: true },
    { id: "b6", title: "评审专家倾向性分析方法论", tags: ["策略"], date: "2024-02", premium: true },
  ],
  images: [
    { id: "i1", title: "道路横断面标准图", tags: ["道路", "断面"], date: "2024", premium: false },
    { id: "i2", title: "沥青路面结构层次示意图", tags: ["路面", "结构"], date: "2024", premium: false },
    { id: "i3", title: "施工现场平面布置图", tags: ["平面", "布置"], date: "2024", premium: false },
    { id: "i4", title: "基坑支护方案三维效果图", tags: ["基坑", "3D"], date: "2024", premium: true },
    { id: "i5", title: "管线综合排布截面图", tags: ["管网", "截面"], date: "2024", premium: true },
    { id: "i6", title: "安全文明施工标准化图集", tags: ["安全", "图集"], date: "2024", premium: true },
  ],
  craft: [
    { id: "c1", title: "路基处理工艺（换填+强夯）", tags: ["路基", "道路"], date: "2024", premium: false },
    { id: "c2", title: "沥青混凝土路面施工工艺", tags: ["路面", "沥青"], date: "2024", premium: false },
    { id: "c3", title: "钻孔灌注桩施工工艺", tags: ["桩基", "基础"], date: "2024", premium: false },
    { id: "c4", title: "装配式建筑吊装施工工艺", tags: ["装配式", "吊装"], date: "2024", premium: true },
    { id: "c5", title: "深基坑围护施工全流程", tags: ["基坑", "围护"], date: "2024", premium: true },
    { id: "c6", title: "顶管施工关键技术要点", tags: ["管网", "顶管"], date: "2024", premium: true },
  ],
};

/* ========================================
   主页面
   ======================================== */
export default function LibraryPage() {
  const [activeTab, setActiveTab] = useState("business");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");
  const [showPaywall, setShowPaywall] = useState(false);

  const currentTab = LIBRARY_TABS.find((t) => t.id === activeTab)!;
  const items = mockItems[activeTab] || [];
  const filtered = items.filter((item) =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent-violet)] flex items-center justify-center">
                <FolderTree className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold tracking-tight">资料库中心</span>
            </div>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-default)] text-xs text-[var(--text-secondary)] hover:text-white transition-all">
            <Upload className="w-3.5 h-3.5" />
            上传资料
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* 六大库切换标签 */}
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-2 mb-6">
          {LIBRARY_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`p-3 rounded-xl border text-left transition-all ${
                activeTab === tab.id
                  ? "border-[var(--primary)] bg-[var(--primary-glow)]"
                  : "border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)]"
              }`}
            >
              <tab.icon className="w-4 h-4 mb-1.5" style={{ color: tab.color }} />
              <p className="text-xs font-medium truncate">{tab.label}</p>
              <p className="text-[10px] text-[var(--text-tertiary)]">{tab.count} 条</p>
            </button>
          ))}
        </div>

        {/* 搜索 + 筛选 */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <input
              type="text"
              placeholder={`在 ${currentTab.label} 中搜索...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-sm text-white placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--primary)] transition-all"
            />
          </div>
          <button className="p-2 rounded-lg border border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:text-white transition-all">
            <Filter className="w-4 h-4" />
          </button>
          <div className="flex rounded-lg border border-[var(--border-subtle)] overflow-hidden">
            <button onClick={() => setViewMode("list")} className={`p-2 ${viewMode === "list" ? "bg-[var(--bg-surface)] text-white" : "text-[var(--text-tertiary)]"}`}>
              <List className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setViewMode("grid")} className={`p-2 ${viewMode === "grid" ? "bg-[var(--bg-surface)] text-white" : "text-[var(--text-tertiary)]"}`}>
              <Grid3x3 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 资料列表 */}
        <div className={viewMode === "grid" ? "grid grid-cols-2 lg:grid-cols-3 gap-3" : "space-y-2"}>
          {filtered.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className={`group rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-default)] transition-all cursor-pointer ${
                viewMode === "grid" ? "p-4" : "flex items-center gap-4 p-4"
              }`}
            >
              {/* 图标 */}
              <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${currentTab.color}15` }}>
                <FileText className="w-4 h-4" style={{ color: currentTab.color }} />
              </div>

              {/* 内容 */}
              <div className={`flex-1 min-w-0 ${viewMode === "grid" ? "mt-2.5" : ""}`}>
                <h3 className="text-sm font-medium truncate">{item.title}</h3>
                <div className="flex items-center gap-2 mt-1">
                  {item.tags.map((tag) => (
                    <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-tertiary)]">{tag}</span>
                  ))}
                </div>
              </div>

              {/* 操作 */}
              <div className="flex items-center gap-2 shrink-0">
                {item.premium && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] bg-amber-500/10 text-amber-400">
                    <Lock className="w-2.5 h-2.5" /> 会员
                  </span>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (item.premium) setShowPaywall(true);
                  }}
                  className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-white hover:bg-[var(--bg-surface)] transition-all opacity-0 group-hover:opacity-100"
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* 当前分类说明 */}
        <div className="mt-6 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <currentTab.icon className="w-5 h-5" style={{ color: currentTab.color }} />
            <div>
              <p className="text-xs font-medium">{currentTab.label}</p>
              <p className="text-[10px] text-[var(--text-tertiary)]">{currentTab.desc}</p>
            </div>
          </div>
          <span className="text-xs text-[var(--text-tertiary)]">
            共 {currentTab.count} 条 · 免费 {items.filter((i) => !i.premium).length} 条 · 会员 {items.filter((i) => i.premium).length} 条
          </span>
        </div>
      </main>

      {/* 付费墙弹窗 */}
      <PaywallModal isOpen={showPaywall} onClose={() => setShowPaywall(false)} trigger="library" />
    </div>
  );
}
