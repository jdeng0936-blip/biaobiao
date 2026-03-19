"use client";
/**
 * 标标 AI · 全局项目状态管理（Zustand）
 *
 * 替代 localStorage 零散存取，统一管理跨 Step 共享数据。
 * 所有 Step 组件通过 useProjectStore() hook 读写状态。
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

/* ========================================
   类型定义
   ======================================== */

/** 评分点 */
export interface ScoringPoint {
  id: string;
  category: string;
  item: string;
  maxScore: number;
  description: string;
}

/** 大纲章节 */
export interface OutlineSection {
  id: string;
  title: string;
  type: string;       // technical / quality / safety / schedule / overview
  scoringRef?: string; // 关联的评分点 ID
}

/** 反AI审查结果 */
export interface ReviewResult {
  sectionId: string;
  riskLevel: "low" | "medium" | "high";
  aiProbability: number;
  suggestions: string[];
}

/** 项目全局状态 */
interface ProjectState {
  // ─── 项目标识 ───
  projectId: string;         // 后端项目 UUID（new 时为空）

  // ─── Step 1: 项目设置 ───
  projectName: string;
  bidType: string;
  industry: string;

  // ─── Step 2: 文件上传 ───
  uploadedFiles: Array<{
    name: string;
    size: number;
    chunksCreated: number;
    uploadedAt: string;
  }>;

  // ─── Step 3: 评分点 + 大纲 ───
  scoringPoints: ScoringPoint[];
  outlineSections: OutlineSection[];
  totalScore: number;

  // ─── Step 4: 生成内容 ───
  generatedContent: Record<string, string>;  // sectionId → 生成的文本

  // ─── Step 5: 审查结果 ───
  reviewResults: ReviewResult[];

  // ─── Actions ───
  setProjectId: (id: string) => void;
  setProjectInfo: (name: string, bidType: string, industry: string) => void;
  addUploadedFile: (file: { name: string; size: number; chunksCreated: number }) => void;
  setScoringData: (points: ScoringPoint[], totalScore: number) => void;
  setOutline: (sections: OutlineSection[]) => void;
  setGeneratedContent: (sectionId: string, content: string) => void;
  setReviewResults: (results: ReviewResult[]) => void;
  resetProject: () => void;
}

/* ========================================
   初始状态
   ======================================== */
const initialState = {
  projectId: "",
  projectName: "",
  bidType: "",
  industry: "",
  uploadedFiles: [],
  scoringPoints: [],
  outlineSections: [],
  totalScore: 0,
  generatedContent: {},
  reviewResults: [],
};

/* ========================================
   Store 定义（含 persist 持久化到 localStorage）
   ======================================== */
export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      ...initialState,

      // ─── 项目标识 ───
      setProjectId: (id) =>
        set({ projectId: id }),

      // ─── Step 1 ───
      setProjectInfo: (name, bidType, industry) =>
        set({ projectName: name, bidType, industry }),

      // ─── Step 2 ───
      addUploadedFile: (file) =>
        set((state) => ({
          uploadedFiles: [
            ...state.uploadedFiles,
            { ...file, uploadedAt: new Date().toISOString() },
          ],
        })),

      // ─── Step 3 ───
      setScoringData: (points, totalScore) =>
        set({ scoringPoints: points, totalScore }),

      setOutline: (sections) =>
        set({ outlineSections: sections }),

      // ─── Step 4 ───
      setGeneratedContent: (sectionId, content) =>
        set((state) => ({
          generatedContent: { ...state.generatedContent, [sectionId]: content },
        })),

      // ─── Step 5 ───
      setReviewResults: (results) =>
        set({ reviewResults: results }),

      // ─── Reset ───
      resetProject: () => set(initialState),
    }),
    {
      name: "biaobiao-project-store",  // localStorage key
      storage: createJSONStorage(() => localStorage),
      // 只持久化关键数据，不持久化中间态
      partialize: (state) => ({
        projectId: state.projectId,
        projectName: state.projectName,
        bidType: state.bidType,
        industry: state.industry,
        uploadedFiles: state.uploadedFiles,
        scoringPoints: state.scoringPoints,
        outlineSections: state.outlineSections,
        totalScore: state.totalScore,
        generatedContent: state.generatedContent,
      }),
    }
  )
);
