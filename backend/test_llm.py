import httpx
import json
import asyncio

async def test_stream():
    url = "http://localhost:8001/api/v1/generate/section"
    payload = {
        "section_title": "1.1 编制依据与原则",
        "section_type": "technical",
        "project_name": "滨海大道二标段工程",
        "project_type": "市政道路",
        "requirements": "请强调响应绿色低碳环保要求",
        "use_rag": False
    }

    print(f"Connecting to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("POST", url, json=payload, timeout=60.0) as response:
                print(f"Status: {response.status_code}")
                # 逐行读取 SSE (Server-Sent Events)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:] # 去掉 data: 
                        try:
                            # 尝试解析 JSON
                            data = json.loads(data_str)
                            if data.get("type") == "content":
                                # 正常打出一段流片段（保持同一行打印）
                                print(data.get("text", ""), end="", flush=True)
                            elif data.get("type") == "done":
                                print("\n\n[SSE 流式接收完毕 - DONE信号]")
                            elif data.get("type") == "error":
                                print(f"\n[STREAM ERROR] {data.get('message')}")
                        except json.JSONDecodeError:
                            # 也有可能是纯文本 data (比如我们出错了)
                            print(data_str)
        except Exception as e:
            print(f"连接失败或抛错: {e}")

if __name__ == "__main__":
    asyncio.run(test_stream())
