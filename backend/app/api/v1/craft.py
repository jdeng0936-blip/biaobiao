"""
API 路由 — 施工工艺图谱
提供工艺树查询、工艺节点详情、高分范文检索。
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/craft", tags=["施工工艺图谱"])


# ──────────────────────────── 数据模型 ────────────────────────────

class CraftMethod(BaseModel):
    """施工工法"""
    name: str
    suitability: str
    difficulty: str  # 低/中/高
    cost: str  # 低/中/高


class CraftParameter(BaseModel):
    """技术参数"""
    name: str
    standard: str
    source: str


class CraftDetail(BaseModel):
    """工艺节点详情"""
    id: str
    title: str
    category: str
    methods: list[CraftMethod]
    workflow: list[str]
    parameters: list[CraftParameter]
    risks: list[str]
    high_score_paragraph: str


# ──────────────────────────── 内置工艺知识库 ────────────────────────────

CRAFT_DB: dict[str, CraftDetail] = {
    "roadbed": CraftDetail(
        id="roadbed",
        title="路基处理工艺",
        category="市政工程 > 道路工程 > 路基处理",
        methods=[
            CraftMethod(name="换填法", suitability="软弱地基，深度≤3m", difficulty="低", cost="中"),
            CraftMethod(name="强夯法", suitability="杂填土/湿陷性黄土", difficulty="中", cost="低"),
            CraftMethod(name="CFG桩复合地基", suitability="深层软基，深度3-15m", difficulty="高", cost="高"),
            CraftMethod(name="水泥搅拌桩", suitability="淤泥质软土", difficulty="中", cost="中"),
            CraftMethod(name="预压法", suitability="大面积软基处理", difficulty="低", cost="低"),
        ],
        workflow=["场地清表 → 测量放线", "原地面处理/清淤", "分层回填压实（每层≤30cm）", "压实度检测（≥93%）", "弯沉值检测验收"],
        parameters=[
            CraftParameter(name="压实度", standard="≥93%（路床顶面≥96%）", source="JTG F10-2006"),
            CraftParameter(name="弯沉值", standard="≤200（0.01mm）", source="设计文件"),
            CraftParameter(name="CBR 值", standard="≥8%（上路床）", source="JTG D30-2015"),
            CraftParameter(name="填料最大粒径", standard="≤100mm", source="JTG F10-2006"),
        ],
        risks=["路基不均匀沉降 — 控制措施：分层碾压+沉降观测", "边坡滑塌 — 控制措施：合理放坡+排水设施", "弹簧土 — 控制措施：翻挖晾晒+掺灰处理"],
        high_score_paragraph="本工程路基处理采用\"换填+强夯\"组合工艺。路基范围内先清除表土30cm，对软弱地基段（K2+100~K2+380）采用换填碎石垫层，厚度50cm，分两层压实，压实度不低于96%。对杂填土段（K3+200~K3+500）采用强夯法处理,夯击能2000kN·m,每点夯击8~10击,最后两击平均夯沉量不超过50mm。",
    ),
    "pavement": CraftDetail(
        id="pavement",
        title="路面结构工艺",
        category="市政工程 > 道路工程 > 路面结构",
        methods=[
            CraftMethod(name="沥青混凝土路面", suitability="城市主干道/快速路", difficulty="中", cost="高"),
            CraftMethod(name="水泥混凝土路面", suitability="重载交通/收费站", difficulty="中", cost="中"),
            CraftMethod(name="半刚性基层+沥青面层", suitability="一般市政道路", difficulty="中", cost="中"),
        ],
        workflow=["基层施工/养护", "透层油喷洒", "下面层摊铺碾压", "粘层油喷洒", "上面层摊铺碾压", "标线施划"],
        parameters=[
            CraftParameter(name="压实度", standard="≥96%（马歇尔密度）", source="JTG F40-2004"),
            CraftParameter(name="平整度", standard="≤2mm（3m直尺）", source="JTG F80/1-2004"),
            CraftParameter(name="摊铺温度", standard="≥150°C", source="JTG F40-2004"),
        ],
        risks=["路面裂缝 — 控制措施：控制摊铺温度+接缝处理", "车辙变形 — 控制措施：改性沥青+合理级配"],
        high_score_paragraph="本工程路面采用\"水泥稳定碎石基层+改性沥青面层\"双层结构。基层采用C30水泥稳定碎石，厚度36cm分两层施工，7天无侧限抗压强度不低于4.0MPa。面层采用SBS改性沥青AC-13+AC-20双层结构，总厚度11cm。",
    ),
    "pile": CraftDetail(
        id="pile",
        title="桩基础工艺",
        category="房建工程 > 基础工程 > 桩基础",
        methods=[
            CraftMethod(name="钻孔灌注桩", suitability="各类地层", difficulty="中", cost="高"),
            CraftMethod(name="预制管桩", suitability="软土/砂土", difficulty="低", cost="中"),
            CraftMethod(name="旋挖桩", suitability="黏土/砂土层", difficulty="中", cost="中"),
            CraftMethod(name="人工挖孔桩", suitability="硬质岩层/无水", difficulty="高", cost="低"),
        ],
        workflow=["桩位放样", "护筒埋设", "钻孔/成孔", "清孔检测", "钢筋笼安装", "混凝土浇筑", "桩基检测"],
        parameters=[
            CraftParameter(name="桩身混凝土强度", standard="≥C30（水下 C35）", source="JGJ 94-2008"),
            CraftParameter(name="桩位偏差", standard="≤50mm", source="JGJ 94-2008"),
            CraftParameter(name="桩身垂直度", standard="≤1%", source="JGJ 94-2008"),
        ],
        risks=["断桩 — 控制措施：连续浇筑+导管法", "缩径 — 控制措施：控制泥浆比重", "桩底沉渣 — 控制措施：二次清孔"],
        high_score_paragraph="本工程基础采用钻孔灌注桩，桩径φ800mm，桩长22-28m，持力层为中风化花岗岩。采用旋挖钻机成孔，泥浆护壁，混凝土水下浇筑工艺。钢筋笼主筋采用HRB400级φ25mm，箍筋φ8@200mm。单桩竖向承载力特征值≥3500kN。",
    ),
}


# ──────────────────────────── 接口实现 ────────────────────────────

@router.get("/tree")
async def get_craft_tree():
    """获取工艺知识树结构"""
    return {
        "tree": [
            {
                "id": "municipal", "label": "市政工程",
                "children": [
                    {"id": "road", "label": "道路工程", "children": [
                        {"id": "roadbed", "label": "路基处理", "docCount": 24, "score": 92},
                        {"id": "pavement", "label": "路面结构", "docCount": 18, "score": 89},
                        {"id": "drainage", "label": "排水系统", "docCount": 15, "score": 87},
                    ]},
                    {"id": "bridge", "label": "桥梁工程", "children": [
                        {"id": "substructure", "label": "下部结构", "docCount": 12, "score": 91},
                        {"id": "superstructure", "label": "上部结构", "docCount": 14, "score": 90},
                    ]},
                ],
            },
            {
                "id": "building", "label": "房建工程",
                "children": [
                    {"id": "foundation", "label": "基础工程", "children": [
                        {"id": "pile", "label": "桩基础", "docCount": 16, "score": 93},
                        {"id": "raft", "label": "筏板基础", "docCount": 10, "score": 90},
                    ]},
                    {"id": "structure", "label": "主体结构", "children": [
                        {"id": "frame", "label": "框架结构", "docCount": 20, "score": 91},
                        {"id": "shearwall", "label": "剪力墙结构", "docCount": 15, "score": 92},
                    ]},
                ],
            },
        ],
        "total_nodes": 248,
    }


@router.get("/detail/{craft_id}")
async def get_craft_detail(craft_id: str):
    """获取工艺节点详情"""
    detail = CRAFT_DB.get(craft_id)
    if not detail:
        return {"error": "未找到该工艺节点", "id": craft_id}
    return detail.model_dump()


@router.get("/search")
async def search_craft(q: str = ""):
    """搜索工艺节点"""
    if not q:
        return {"results": []}
    results = [d.model_dump() for d in CRAFT_DB.values() if q.lower() in d.title.lower() or q.lower() in d.category.lower()]
    return {"results": results, "count": len(results)}
