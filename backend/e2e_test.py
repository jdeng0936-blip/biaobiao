"""
标标 AI — 端到端 API 集成测试 (原生依赖版)
运行方式: python3 e2e_test.py
"""
import urllib.request
import urllib.error
import json
import uuid
import sys

API_BASE = "http://localhost:8001"

def print_step(msg):
    print(f"\n➤ {msg}")

def print_success(msg):
    print(f"✔ {msg}")

def print_error(msg):
    print(f"✘ {msg}")
    sys.exit(1)

def do_request(method, path, body=None):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, method=method)
    if body:
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(body).encode('utf-8')
        req.data = data
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body) if res_body else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        print_error(f"无法连接服务端: {str(e)}")

def main():
    print("==========================================")
    print("      标标 AI - 全链路 API 集成测试        ")
    print("==========================================\n")

    # 1. 检查健康状态
    print_step("1. 检查系统健康检查接口 (/health)")
    status, data = do_request("GET", "/health")
    if status == 200:
        print_success(f"Health OK: {data}")
    else:
        print_error(f"Health Failed: {status}")

    # 2. 创建标书项目
    print_step("2. 创建标书项目 (POST /projects)")
    project_name = f"E2E 自动化测试项目 - {str(uuid.uuid4())[:6]}"
    status, data = do_request("POST", "/projects", {
        "name": project_name,
        "project_type": "municipal_road"
    })
    if status == 200:
        project_id = data["id"]
        print_success(f"项目创建成功 | ID: {project_id} | Name: {project_name}")
    else:
        print_error(f"项目创建失败: {data}")

    # 3. 获取项目列表
    print_step("3. 获取项目列表 (GET /projects)")
    status, data = do_request("GET", "/projects")
    if status == 200:
        print_success(f"成功获取项目列表 | 共 {len(data)} 个项目")
    else:
        print_error(f"获取项目列表失败: {data}")

    # 4. 获取工艺图谱
    print_step("4. 获取施工工艺树 (GET /craft/tree)")
    status, data = do_request("GET", "/craft/tree")
    if status == 200:
        nodes = data.get("total_nodes", 0)
        print_success(f"工艺图谱加载正常 | 共 {nodes} 个工艺节点")
    else:
        print_error(f"工艺图谱加载失败: {data}")

    # 5. 获取变体维度
    print_step("5. 获取变体引擎配置 (GET /variants/dimensions)")
    status, data = do_request("GET", "/variants/dimensions")
    if status == 200:
        dims = len(data.get("dimensions", []))
        print_success(f"变体配置加载正常 | 共 {dims} 个控制维度")
    else:
        print_error(f"变体配置加载失败: {data}")

    # 6. 反审标接口
    print_step("6. 测试反审标检测 (POST /api/v1/anti-review/check)")
    long_text = "测试一段包含敏感废标词的文本: 定向指定某品牌设备。这是为了满足反审标接口所要求的最小 50 个字符的特征限制。在编写标书或者招标文件的时候，一定要注意避免出现具有排他性的词汇和指定唯一供应商的描述以免导致废标。"
    status, data = do_request("POST", "/api/v1/anti-review/check", {"text": long_text})
    if status == 200:
        print_success(f"反审标检测成功 | 安全分: {data.get('score')} | 建议: {data.get('metrics', {}).get('compliance', 'N/A')}")
    else:
        print_error(f"反审标检测失败: {data}")

    print("\n==========================================")
    print("🎉 End-to-End 测试全部通过！系统稳如老狗。")
    print("==========================================\n")

if __name__ == "__main__":
    main()
