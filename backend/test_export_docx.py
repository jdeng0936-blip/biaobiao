import os
from app.services.export_service import BidExportService

def test_export():
    service = BidExportService()
    
    project_name = "南京奥体中心维修及附属设施改造工程"
    company_name = "江苏某某建筑建设集团有限公司"
    sections = {
        "一、工程概况与整体部署": (
            "1.1 工程概况\n"
            "本工程位于南京市建邺区江东中路222号，主要涉及场馆防水维修、看台座椅更换以及外立面灯光改造。\n\n"
            "（一）工程重难点分析\n"
            "本工程的重难点在于高空作业多，交叉施工范围广。必须协调好土建与机电安装的流水穿插作业。\n\n"
        ),
        "二、主要施工方案": (
            "2.1 防水工程施工方案\n"
            "1. 屋面防水层采用 4mm 厚 SBS 改性沥青防水卷材。\n"
            "2. 施工前表面应清理干净，确保含水率低于 9%。\n\n"
            "2.2 钢结构除锈防腐方案\n"
            "采用高压水刀除锈至 Sa2.5 级，并立刻涂装富锌底漆两道，中间漆一道，聚氨酯面漆两道。\n"
        )
    }

    try:
        docx_bytes = service.export_document(project_name, sections, company_name)
        with open("test_output.docx", "wb") as f:
            f.write(docx_bytes)
        print(f"成功导出 DOCX 文件！大小: {len(docx_bytes)} 字节")
    except Exception as e:
        print("Docx 导出失败:", e)

if __name__ == "__main__":
    test_export()
