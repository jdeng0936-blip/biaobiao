import httpx
import asyncio
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_sample_pdf(filename="sample_bid.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    # 添加足够的文字使得能够被切成至少一个 chunk (min_chunk_size=100)
    text = (
        "第一章 施工方案与技术措施\n"
        "1.1 混凝土工程施工方案\n"
        "本项目采用 C35 标号抗渗混凝土，抗渗等级不低于 P8。为了防止大体积混凝土裂缝，"
        "在浇筑时严格控制入模温度不高于 28°C，内外温差不超过 25°C。采用分层跳仓法施工，"
        "每层浇筑厚度控制在 500mm 以内。养护时间不少于 14 d，表面覆盖塑料薄膜和保温棉毡。"
        "同时在混凝土内部预埋测温线，实时记录混凝土升降温曲线，指导养护工作。\n\n"
        "第二章 安全文明施工\n"
        "要求现场实现100%封闭围挡，高度不低于2.5米。扬尘监控系统全天候运行，遇到 PM10 超标"
        "自动开启喷淋降尘系统。严禁在夜间 22:00 - 06:00 进行高噪音的中大型施工设备作业。"
    )
    y = 800
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 25
    c.save()

async def run_test():
    url = "http://localhost:8001/api/v1/upload/document"
    pdf_file = "sample_bid.pdf"
    
    # 1. 创建测试 PDF
    create_sample_pdf(pdf_file)
    print(f"Uploading {pdf_file} to {url} ...")

    # 2. 发送上传请求
    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file, f, "application/pdf")}
            try:
                resp = await client.post(url, files=files)
                print("Status:", resp.status_code)
                print("Response:", resp.json())
            except Exception as e:
                print("Error during upload:", e)
                
    # 3. 清理
    if os.path.exists(pdf_file):
        os.remove(pdf_file)

if __name__ == "__main__":
    asyncio.run(run_test())
