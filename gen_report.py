import subprocess, sys
from pathlib import Path
try:
    from docx import Document
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx", "-q"])
    from docx import Document

from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.font.size = Pt(11)

def add_title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.size = Pt(18)
    r.bold = True

def add_h1(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(14)
    r.bold = True

def add_h2(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(12)
    r.bold = True

def add_text(text):
    doc.add_paragraph(text)

def add_items(items):
    for item in items:
        doc.add_paragraph(item, style="List Number")

add_title("AI冰箱管家与剩菜改造师")
add_title("项目选型流程")

add_h1("一、整理需求与MVP")

add_h2("（一）用户—场景—痛点")
add_text("独居年轻人、小家庭、宿舍党在日常做饭中，买回来的蔬菜放两天就忘了；冰箱里剩半颗白菜、两个鸡蛋、一点米饭，不知道怎么做；经常因为食材过期造成浪费；想做饭但不想再出门买菜；一个人吃饭很难控制分量。核心痛点是食材浪费严重、做饭决策成本高、剩菜不知如何处理。")

add_h2("（二）MVP核心功能")
add_items([
    "拍照识别食材：打开App拍一张冰箱、餐桌或购物袋照片，AI自动识别里面的食材，用户确认数量、购买日期、存放位置、是否开封；",
    '食材保质期管理：根据食材类型估算保质期（叶菜2-3天、根茎5-7天、蛋奶2-4周等），生成「即将过期/仍可存放/建议冷冻/已过期」食材时间线，提醒优先处理快过期食材；',
    '剩菜改造推荐：用户点击「今天吃什么」，AI根据现有食材+偏好（清淡/快手/热食）生成2-3个菜谱，含步骤、用时、难度、是否需额外采购；',
    "浪费统计看板：本周过期食材数量、成功消耗数量、预估节约金额、减少碳排放估算、连续节约天数。",
])

add_h1("二、初步选型")
add_text("产品形态：网页应用（Streamlit社区云部署，手机/电脑浏览器直接打开，不用安装APP）。")
add_text("初步技术栈：Python Streamlit前端 + 智谱GLM-4V（识图）+ GLM-4-Flash（菜谱生成）大模型 + JSON本地存储，开发工具Visual Studio Code。")

add_h1("三、AI顾问校验结果")

add_h2("（一）方案评价与修改建议")
add_text("优点：整体方向合理，Streamlit+大模型足够支撑一个冰箱食材管理MVP。浏览器打开即可，适合家庭场景；直接调多模态大模型识图，不自训模型，开发快且准确率高；JSON存储单用户够用，部署简单。")
add_text("存在问题：")
add_items([
    "拍照识别完全依赖大模型，遇到光线暗、食材堆叠、小包装可能漏识别，需要用户确认环节兜底；",
    "菜谱生成没有菜谱库支撑，大模型可能生成不地道的做法，奇怪食材组合时质量不稳定；",
    "保质期是硬编码规则，实际同种食材不同品种、不同保存条件差异大；",
    "JSON文件存储不支持多用户、多设备同步，家庭共享场景受限；",
    "浪费统计的金额和碳减排是粗估，没有真实价格数据。",
])
add_text("修改建议：")
add_items([
    "保留Streamlit+大模型整体方案，识别后增加用户确认/编辑/手动补充环节；",
    "保质期规则表覆盖10类常见食材即可，用户可手动调整到期日期；",
    "菜谱生成先用大模型直生成，后续可加菜谱库RAG检索提升地道性；",
    "存储先用JSON，后续需要家庭共享再换SQLite或云端数据库；",
    "统计看板的金额和碳减排用估算值，比赛演示足够，后续可接入真实价格。",
])

add_h2("（二）开发任务")
add_text("①简单：")
add_items([
    "安装Python 3.13、VS Code（含Python扩展），创建项目目录；",
    "安装Streamlit、openai SDK、pillow、python-dotenv，申请智谱API Key；",
    "写Streamlit首页，跑通四标签页框架（拍照识别/冰箱管理/今天吃什么/浪费统计）；",
    "创建保质期规则表shelf_life.json，定义10类食材的冷藏/冷冻/常温保质期天数；",
    "实现JSON存储层，支持食材增删改查、消耗记录、过期日志。",
])
add_text("②中等：")
add_items([
    "封装智谱GLM大模型调用（OpenAI兼容格式），实现chat文本生成和chat_vision图像识别；",
    "实现拍照识别：图片转base64发给GLM-4V，解析返回的JSON食材列表，前端支持上传/确认/批量入库；",
    "实现保质期计算：根据食材类别匹配保质期规则，计算剩余天数和状态（已过期/即将过期/建议冷冻/仍可存放），生成时间线分组展示；",
    "实现菜谱生成：将现有食材+用户偏好构造prompt发给GLM-4-Flash，解析返回的JSON菜谱（含步骤/用时/难度/热量/份量/额外采购清单）；",
    "实现浪费统计：本周过期数、成功消耗数、节约金额、连续节约天数、碳减排估算，看板展示。",
])
add_text("③困难：")
add_items([
    "改造为Streamlit单体应用，前端直接import后端模块，去掉FastAPI HTTP调用，一键启动；",
    "配置部署：.gitignore排除密钥，streamlit_app.py入口文件，.streamlit/secrets.toml密钥配置；",
    "部署到Streamlit社区云，连接GitHub仓库，配置Secrets，验证公开链接可访问；",
    "补充单元测试：保质期计算、分类匹配、JSON解析、统计逻辑，覆盖率>80%；",
    "如果要支持家庭多人共享，引入SQLite+用户标识，食材和消耗记录按用户隔离。",
])

add_h1("四、最终锁定方案")
add_text("本项目产品形态为网页应用，采用Python Streamlit单体架构，拍照识别使用智谱GLM-4V多模态大模型，菜谱生成使用智谱GLM-4-Flash，保质期管理使用10类食材规则引擎，数据存储使用JSON文件，部署到Streamlit社区云。用户打开网页后可以拍照识别食材、查看保质期时间线、根据现有食材生成菜谱、查看本周浪费统计，全程不需要安装任何应用，手机浏览器直接使用。")

out = str(Path(__file__).resolve().parent / "AI冰箱管家与剩菜改造师_项目选型流程.docx")
doc.save(out)
print("已生成:", out)