#!/bin/bash
# =====================================================
# md2pdf.sh — Markdown 批量转 PDF（Chrome 无头模式）
# 使用方法：
#   ./md2pdf.sh                    # 转换当前目录所有 .md 文件
#   ./md2pdf.sh 战略共创商业合作意向书.md  # 转换单个文件
# 输出文件保存在 ./PDF_output/ 目录
# =====================================================

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DOCS_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$DOCS_DIR/PDF_output"
mkdir -p "$OUTPUT_DIR"

# 企业蓝主题 CSS
CSS='body{font-family:"PingFang SC","Microsoft YaHei",Arial,sans-serif;max-width:920px;margin:0 auto;padding:40px 60px;color:#1a1a2e;line-height:1.85;font-size:15px}
h1{color:#0d47a1;font-size:26px;border-bottom:3px solid #0d47a1;padding-bottom:12px;margin-top:40px}
h2{color:#1565c0;font-size:20px;border-left:5px solid #1565c0;padding-left:12px;margin-top:36px}
h3{color:#1976d2;font-size:16px;margin-top:24px}
h4{color:#333;font-size:15px}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px}
th{background:#1565c0;color:white;padding:10px 14px;text-align:left}
td{border:1px solid #dde3f0;padding:9px 14px}
tr:nth-child(even){background:#f0f4ff}
blockquote{border-left:4px solid #1976d2;background:#e8f0fe;padding:12px 16px;margin:16px 0;border-radius:0 6px 6px 0;color:#1a237e}
code,pre{font-family:Menlo,monospace;font-size:13px;background:#1a1a2e;color:#e8eaf6;border-radius:6px}
pre{padding:16px 20px;overflow-x:auto;line-height:1.6}
hr{border:none;border-top:2px solid #dde3f0;margin:32px 0}
strong{color:#0d47a1}'

convert_one() {
    local md_file="$1"
    local name
    name="$(basename "$md_file" .md)"
    local tmp_html="/tmp/_md2pdf_${name}.html"
    local out_pdf="$OUTPUT_DIR/${name}.pdf"

    # md → html
    pandoc "$md_file" -o "$tmp_html" --standalone \
        --metadata title="$name" \
        --css=/dev/stdin <<< "$CSS"

    # html → pdf（Chrome 无头）
    "$CHROME" --headless=new --disable-gpu --no-sandbox \
        --print-to-pdf="$out_pdf" \
        --print-to-pdf-no-header "$tmp_html" 2>/dev/null

    rm -f "$tmp_html"

    if [ -f "$out_pdf" ]; then
        size=$(du -h "$out_pdf" | cut -f1)
        echo "✅ $name.pdf  ($size)"
    else
        echo "❌ 转换失败: $md_file"
    fi
}

# 判断参数
if [ "$#" -gt 0 ]; then
    for arg in "$@"; do
        convert_one "$arg"
    done
else
    echo "🚀 批量转换 $DOCS_DIR 下所有 .md 文件..."
    for md in "$DOCS_DIR"/*.md; do
        convert_one "$md"
    done
fi

echo ""
echo "📁 PDF 输出目录: $OUTPUT_DIR"
open "$OUTPUT_DIR"
