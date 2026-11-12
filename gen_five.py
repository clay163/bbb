from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.font.size = Pt(11)

def title(text, size=18):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.font.size = Pt(size); r.bold = True

def h1(text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(14); r.bold = True

def h2(text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(12); r.bold = True

def para(text):
    doc.add_paragraph(text)

def numbered(items):
    for item in items:
        doc.add_paragraph(item, style="List Number")

def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers), style="Table Grid")
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = h
        for p in c.paragraphs:
            for r in p.runs: r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = v
    doc.add_paragraph()

title("AI冰箱管家与剩菜改造师 · 专项方案")
title("项目选型流程", 14)
para("")

para("基于多模态大模型与保质期规则引擎，面向家庭食材管理、剩菜改造与浪费减少等场景，提供拍照识别、保质期管理、菜谱生成与浪费统计四大核心功能。各模块围绕用户需求、业务流程、系统架构、技术接入、数据资料、实施计划和验收标准展开。")

h1("1. 平台与建设思路")
para("通用版提供拍照上传、大模型多模态识别（GLM-4V）、文本生成（GLM-4-Flash）、保质期规则引擎、JSON本地存储与统计看板。专项建设通过食材分类匹配、保质期计算、菜谱Prompt构造与证据表达规则，将这些能力组织为面向家庭食材管理的使用流程。")
para("用户拍照或手动输入食材并确认数量、购买日期与存放位置，系统自动匹配食材类别并估算保质期，生成时间线分组展示；用户选择现有食材并填写口味偏好，AI生成含步骤、用时、难度与额外采购清单的菜谱；消耗与过期记录自动汇总为浪费统计看板。")

h1("2. 专项方向")
table(
    ["功能模块", "主要用户", "核心功能", "输入材料"],
    [
        ["拍照识别", "所有用户", "食材自动识别、数量确认、批量入库", "冰箱/餐桌/购物袋照片"],
        ["保质期管理", "所有用户", "保质期估算、时间线分组、过期提醒", "食材名称、购买日期、存放位置、是否开封"],
        ["剩菜改造", "想做饭的用户", "根据现有食材+偏好生成菜谱", "食材列表、口味偏好（清淡/快手/热食）"],
        ["浪费统计", "所有用户", "过期/消耗统计、节约金额、碳减排估算", "消耗记录、过期记录"],
    ]
)

h1("3. 共享架构与业务链路")

h2("交互层")
para("Streamlit四标签页：拍照识别、冰箱管理、今天吃什么、浪费统计。用户上传照片后确认识别结果并批量入库；冰箱管理以时间线分组展示食材状态（已过期/即将过期/建议冷冻/仍可存放），支持手动添加、消耗与删除；今天吃什么页面选择食材与偏好后生成菜谱卡片；浪费统计展示本周指标与环保反馈。")

h2("AI与工具层")
para("拍照识别通过GLM-4V多模态大模型，图片转base64后发送识别Prompt，返回JSON格式的食材列表（名称、数量、存放位置）。菜谱生成通过GLM-4-Flash，构造包含现有食材与用户偏好的Prompt，返回JSON格式的菜谱（菜名、步骤、用时、难度、热量、份量、额外采购清单）。识别与生成结果均带用户确认环节，失败时降级处理不中断流程。")

h2("数据与规则层")
para("食材数据存储在JSON文件中，包含食材信息、消耗记录与过期日志。保质期规则表定义10类常见食材（叶菜类、根茎类、瓜果类、蛋奶类、肉类、水产类、主食类、熟食类、干货类、水果类）的冷藏/冷冻/常温保质期天数与存储建议。开封食材保质期减半，未匹配类别兜底为3天。")

h2("运行部署")
para("Streamlit单体应用，本地运行仅需streamlit run streamlit_app.py一条命令。API Key通过.env文件或Streamlit secrets管理。部署到Streamlit社区云后获得永久公开链接，公网访问也可通过serveo.net SSH隧道临时暴露。单元测试覆盖5个核心模块，105个测试用例，覆盖率99.3%。")

h1("4. 实施计划与验证")
table(
    ["阶段", "建设任务", "阶段产出"],
    [
        ["需求定义", "确定核心功能、10类食材保质期规则、数据模型", "规则表shelf_life.json、食材与菜谱数据模型"],
        ["核心开发", "实现大模型封装、保质期计算、拍照识别、菜谱生成、浪费统计", "app/下7个模块，可调用的业务逻辑"],
        ["前端联调", "开发Streamlit四标签页、单体入口、部署配置", "streamlit_app.py入口、.gitignore、secrets配置"],
        ["测试验证", "补充单元测试、端到端集成测试、部署验证", "105个测试通过、99.3%覆盖率、demo闭环跑通"],
        ["部署交付", "GitHub推送、Streamlit社区云部署、公网链接验证", "公开链接、演示数据、操作说明"],
    ]
)
para("验收关注完整使用链路（拍照→识别→入库→保质期→菜谱→统计）、AI生成菜谱是否可用且步骤完整、保质期计算是否覆盖开封与跨存储场景、统计看板数据是否准确、部署后公开链接是否可访问。验证记录包含7种演示食材、3组时间线、3个AI生成菜谱与6项统计指标。")

h1("5. 方案文件与图源")
table(
    ["模块", "文件路径", "说明"],
    [
        ["大模型封装", "app/llm.py", "智谱GLM-4V/GLM-4-Flash，OpenAI兼容格式"],
        ["食材存储", "app/storage.py", "JSON文件持久化，食材CRUD与消耗记录"],
        ["保质期引擎", "app/fridge.py", "分类匹配、保质期计算、时间线分组"],
        ["拍照识别", "app/vision.py", "GLM-4V识图，JSON解析与兜底"],
        ["菜谱生成", "app/recipe.py", "GLM-4-Flash生成菜谱，JSON解析与降级"],
        ["浪费统计", "app/stats.py", "本周过期/消耗/节约金额/连续天数"],
        ["前端界面", "frontend/app.py", "Streamlit四标签页单体应用"],
        ["部署入口", "streamlit_app.py", "社区云入口，绝对路径执行"],
        ["保质期规则", "data/shelf_life.json", "10类食材保质期与存储建议"],
        ["单元测试", "tests/test_*.py", "5个测试文件，105个用例，99.3%覆盖率"],
    ]
)
para("每套包含系统总体架构（单体应用）、前端交互（四标签页）、业务处理（识别→保质期→菜谱→统计）、数据关系（JSON存储+规则表）、AI调用链路（GLM-4V+GLM-4-Flash）与部署架构（Streamlit社区云/SSH隧道）六个方面。演示数据包含7种食材、3组时间线、3个AI生成菜谱与6项统计指标。")

out = r"c:\Users\clay\Desktop\AI冰箱管家_五要素方案报告.docx"
doc.save(out)
print("已生成:", out)