import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "标标 AI — AI 驱动的智能标书制作平台",
  description:
    "全程 AI 赋能的标书制作平台。从招标文件智能解读到高分标书生成，AI 全链路介入，让中标率飙升 500%。",
  keywords: [
    "AI标书",
    "智能标书",
    "标书制作",
    "AI投标",
    "建筑标书",
    "标书生成",
    "招标文件解读",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className={`${inter.variable} dark`}>
      <body>{children}</body>
    </html>
  );
}
