import streamlit as st
import random
import re
import time
import json
import os
from datetime import datetime
import pandas as pd
from openai import OpenAI
import difflib
import docx
import io

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="AI指令词诊断与自动优化工具 v4.0",
    page_icon="🔬",
    layout="wide"
)

# ============================================================
# 数据存储
# ============================================================

HISTORY_DIR = "test_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# ============================================================
# 各年级语言特征配置
# ============================================================

GRADE_CONFIG = {
    "1-2年级": {
        "label": "1-2年级",
        "sentence_len": (5, 15),
        "vocab_level": "生活化",
        "logic_depth": "简单因果",
        "argue_level": "几乎无论证",
        "features": "口语化、重复、依赖具体事例"
    },
    "3年级": {
        "label": "3年级",
        "sentence_len": (8, 20),
        "vocab_level": "开始出现书面词",
        "logic_depth": "单一因果",
        "argue_level": "能说1个理由",
        "features": "连贯表达，论证较浅"
    },
    "4年级": {
        "label": "4年级",
        "sentence_len": (10, 25),
        "vocab_level": "书面词汇增加",
        "logic_depth": "2-3层因果",
        "argue_level": "能说2个理由",
        "features": "逻辑初步清晰，有一定结构"
    },
    "5年级": {
        "label": "5年级",
        "sentence_len": (12, 30),
        "vocab_level": "较丰富",
        "logic_depth": "多角度分析",
        "argue_level": "论证较充分",
        "features": "观点明确，结构完整"
    },
    "6-7年级": {
        "label": "6-7年级",
        "sentence_len": (15, 40),
        "vocab_level": "丰富精准",
        "logic_depth": "深层思辨",
        "argue_level": "论证充分有深度",
        "features": "表达成熟，有思辨性"
    }
}

# ============================================================
# 9种发言类型的配置
# ============================================================

SPEECH_TYPES_CONFIG = [
    {"id": "完整优秀", "desc": "✅ 完整发言（所有维度表现好）"},
    {"id": "观点模糊", "desc": "⚠️ 观点模糊，没有抓住核心矛盾"},
    {"id": "论据空洞", "desc": "⚠️ 观点明确但论据不足"},
    {"id": "逻辑混乱", "desc": "⚠️ 逻辑不清，结构混乱"},
    {"id": "语言粗糙", "desc": "⚠️ 语言表达有问题"},
    {"id": "缺乏共情", "desc": "⚠️ 通情达意出问题，缺少人文关怀"},
    {"id": "只说立场没理由", "desc": "⚠️ 只说立场没有论证"},
    {"id": "跑题抓错矛盾", "desc": "⚠️ 核心方向错误，跑题"},
    {"id": "单维度深挖", "desc": "✅ 部分维度突出，有亮点"}
]

# ============================================================
# 各年级的发言生成模板
# ============================================================

def get_speech_for_grade(grade, speech_type, extracted_data):
    """根据年级和类型生成对应的模拟发言"""
    names = extracted_data.get("names", ["小明", "小丽", "小刚"])
    items = extracted_data.get("items", ["作品", "东西"])
    
    name = random.choice(names) if names else "小明"
    item = random.choice(items) if items else "东西"
    
    templates = {
        "1-2年级": {
            "完整优秀": f"我觉得{name}应该跟对方说对不起，因为弄坏了别人的{item}是不对的。然后他可以问对方要不要帮忙修一下，这样对方就不会那么难过了。",
            "观点模糊": f"我觉得他们两个都有点不对，我也不知道该怎么办，反正就是要和好吧。",
            "论据空洞": f"我觉得{name}应该赔钱，因为弄坏东西就是要赔的，我妈妈说的。",
            "逻辑混乱": f"我觉得……首先呢，{name}是男生，比较皮。然后呢，对方肯定很生气。对了，我觉得老师应该去调解。哦对了……算了，他们两个都有错。",
            "语言粗糙": f"我觉得这事吧，就{name}不对。他跑那么快干啥呀。然后对方也，东西放那儿也不对。就道个歉完事了。",
            "缺乏共情": f"我觉得很简单，{name}弄坏了就要赔。按照规矩办事就行了，不用想那么多。",
            "只说立场没理由": f"我觉得{name}应该道歉。",
            "跑题抓错矛盾": f"我觉得学校应该规定课间不能乱跑，这样就不会发生这种事了。",
            "单维度深挖": f"我觉得{name}应该先问对方'你希望我怎么做'，因为每个人在意的东西不一样。"
        },
        "3年级": {
            "完整优秀": f"我觉得{name}应该先真诚地向对方道歉，因为弄坏了别人的{item}就是不对。然后他可以问问对方，是想要赔钱还是想要帮忙重新做一个。",
            "观点模糊": f"我觉得这件事……嗯……应该要好好处理。反正他们两个都有点不对，我也不知道该怎么办。",
            "论据空洞": f"我觉得{name}应该赔偿对方。因为做错了事就要负责任，我们老师也是这么说的。",
            "逻辑混乱": f"我觉得……首先呢，{name}不应该那么不小心。然后呢，对方肯定很心疼。对了，班长应该去帮忙调解。哦我说到哪里了？",
            "语言粗糙": f"我觉得这事吧，就是{name}不对。他跑那么快干啥呀。反正就他俩的事，好好说说就行了。",
            "缺乏共情": f"我觉得这件事很简单。{name}弄坏了就要赔，按规矩办事。",
            "只说立场没理由": f"我觉得{name}应该赔偿对方的损失。",
            "跑题抓错矛盾": f"我觉得这件事告诉我们，课间不能乱跑。学校应该管得更严一点。",
            "单维度深挖": f"我觉得{name}应该先问问对方最在意的是什么，因为每个人在乎的东西不一样。"
        },
        "4年级": {
            "完整优秀": f"我觉得{name}应该先向对方真诚道歉，因为弄坏别人的{item}就是不对的。然后他要问清楚对方最在意什么——是花了多少钱，还是花了多少时间。然后根据对方的回答，再商量怎么弥补。",
            "观点模糊": f"我觉得这件事双方都有责任，{name}确实不小心，但对方把东西放在那里也有点不小心。我也不知道主要责任在谁。",
            "论据空洞": f"我觉得{name}应该赔偿，因为损坏别人的东西就要赔偿，这是原则。社会上的规则就是这样。",
            "逻辑混乱": f"我觉得……首先，{name}应该反省自己的行为。然后呢，对方也应该理解一下。然后……对了，我觉得老师可以帮忙调解。",
            "语言粗糙": f"我觉得{name}不对，他太不小心了。对方也很难过，东西坏了谁都心疼。但是，呃，大家各退一步就好了。",
            "缺乏共情": f"我觉得这事按规则处理就行了。{name}弄坏了，该赔多少赔多少。没必要考虑那么多情绪因素。",
            "只说立场没理由": f"我觉得{name}应该向对方道歉并赔偿。",
            "跑题抓错矛盾": f"我觉得这件事说明学校的安全管理有问题。如果课间秩序更好一些，就不会发生这种事了。",
            "单维度深挖": f"我觉得{name}应该先了解对方真正的感受和需求。每个人对'失去'的反应不同：有的人最心疼钱，有的人最心疼时间。"
        },
        "5年级": {
            "完整优秀": f"我认为这件事的核心不是赔偿问题，而是{name}能否真诚面对自己的错误。首先，{name}应该主动道歉，要表达自己理解对方的感受。其次，要了解对方最希望得到什么样的弥补。最后，双方一起商量出都能接受的方案。",
            "观点模糊": f"我觉得这件事双方都有一定的责任吧。{name}确实不小心，但对方把东西放在那个位置也不太安全。具体怎么解决，我也说不太清楚。",
            "论据空洞": f"我觉得{name}必须赔偿，因为损坏别人的东西就要赔偿。这是基本的规则和道德要求，不需要讨论。",
            "逻辑混乱": f"关于这件事，我有几个想法。第一，{name}应该道歉。第二，对方也有责任。第三，老师应该参与调解。哦对了，赔偿的问题……反正就是这些吧。",
            "语言粗糙": f"我觉得{name}这事做得不对，他太不小心了。然后对方呢，东西被弄坏了肯定会生气。反正就是各退一步，道个歉赔个钱就解决了。",
            "缺乏共情": f"我认为这是一个简单的责任认定问题。{name}的行为造成了损害，就应该承担相应责任。按照规则赔偿，事情就结束了。",
            "只说立场没理由": f"我认为{name}应当为自己的行为负责，向对方道歉并做出相应赔偿。",
            "跑题抓错矛盾": f"我觉得这件事暴露出学校管理的一个漏洞。如果学校有更完善的安全制度，类似事件就能避免。",
            "单维度深挖": f"我认为这个问题的关键在'换位思考'。{name}需要真正站在对方的立场去感受，只有真正理解了对方的感受，道歉才不会流于形式。"
        },
        "6-7年级": {
            "完整优秀": f"我认为这件事的核心不是简单的赔偿问题，而是关乎责任认知与人际修复的深层议题。首先，{name}需要完成一次真诚的自我反思。其次，双方需要开放地沟通各自的需求与期待。最后，共同制定一个具体的、可执行的修复方案。",
            "观点模糊": f"我觉得这件事要从多个角度来看。一方面，{name}确实有不小心的责任；另一方面，对方把东西放在那里也有一定风险。所以很难说谁全对谁全错。",
            "论据空洞": f"我认为{name}应该承担赔偿责任。因为从基本的社会规则来看，造成他人损失就需要补偿。这个原则不需要讨论。",
            "逻辑混乱": f"我想从几个层面来分析这件事。首先，关于责任归属……嗯，{name}确实有过失。其次，关于解决方式……可能需要道歉和赔偿。总之，这件事给我们的启示是多方面的。",
            "语言粗糙": f"我觉得{name}肯定要道歉啊，这事就是他不对。他太不小心了，把别人辛辛苦苦做的东西弄坏了。反正就是道个歉，该赔多少赔多少。",
            "缺乏共情": f"我认为这是一个典型的责任认定案例。从行为结果来看，{name}造成了损害；从因果关系来看，损害与行为直接相关。因此，按照明确的规则和程序处理即可。",
            "只说立场没理由": f"我认为{name}应当为自己的过失行为承担全部责任，包括诚恳道歉和物质赔偿。",
            "跑题抓错矛盾": f"这件事让我思考的是学校在冲突调解机制上的不足。我们应该把注意力放在制度建设上，而不是个案本身。",
            "单维度深挖": f"我认为这个案例最值得深思的是'同理心'在冲突解决中的核心作用。{name}需要的不是一套应付式的道歉模板，而是真正进入对方的精神世界。"
        }
    }
    
    grade_templates = templates.get(grade, templates["3年级"])
    return grade_templates.get(speech_type, "（发言内容待生成）")


# ============================================================
# 解析上传的脚本
# ============================================================

def parse_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text
    except Exception as e:
        return None


def extract_info_from_script(script_text, api_key, base_url, model):
    if not script_text or len(script_text.strip()) < 10:
        return None
    
    prompt = """
你是一位教育内容分析专家。请从下面的故事脚本中提取以下关键信息：

1. **人物名字**：脚本中出现了哪些小朋友的名字？列出3-5个。
2. **核心矛盾**：脚本中最核心的冲突或矛盾是什么？用一句话概括。
3. **场景**：事件发生的主要场景是什么？
4. **关键物品**：脚本中提到了哪些具体物品？

请严格按以下JSON格式输出：
{
  "names": ["名字1", "名字2", "名字3"],
  "conflict": "核心矛盾一句话概括",
  "scene": "主要场景",
  "items": ["物品1", "物品2"]
}

故事脚本内容：
""" + script_text[:2000]

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位教育内容分析专家。请严格按照JSON格式输出，不要添加任何其他内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        return None


# ============================================================
# AI调用
# ============================================================

def parse_ai_configs(content):
    configs = []
    blocks = re.split(r'={3,}|-{10,}|\n\s*\n\s*\n', content)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        name_line = lines[0].strip()
        name_match = re.search(r'[【\[#]\s*(.+?)\s*[】\]\n]', name_line)
        if name_match:
            name = name_match.group(1).strip()
            prompt = '\n'.join(lines[1:]).strip() if len(lines) > 1 else block
        else:
            name = name_line[:30] if len(name_line) <= 30 else name_line[:27] + "..."
            prompt = '\n'.join(lines[1:]).strip() if len(lines) > 1 else block
        
        role = "未知"
        if "点评" in name or "评价" in name or "反馈" in name:
            role = "点评"
        elif "总结" in name or "归纳" in name:
            role = "总结"
        elif "回应" in name or "对话" in name:
            role = "回应"
        elif "提问" in name or "追问" in name:
            role = "提问"
        elif "鼓励" in name:
            role = "鼓励"
        else:
            role = "其他"
        
        configs.append({"name": name, "role": role, "prompt": prompt})
    return configs


def call_ai(api_key, base_url, model, system_prompt, user_speech):
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_speech}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return "【调用失败】" + str(e)


# ============================================================
# 对比指令词差异
# ============================================================

def highlight_diff(original, optimized):
    if not optimized or not original:
        return optimized, []
    
    orig_lines = original.split('\n')
    opt_lines = optimized.split('\n')
    
    diff = list(difflib.unified_diff(
        orig_lines, opt_lines,
        fromfile='原始', tofile='优化后',
        lineterm=''
    ))
    
    changes = []
    for line in diff:
        if line.startswith('@@'):
            match = re.search(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
            if match:
                old_start = int(match.group(1))
                new_start = int(match.group(2))
                changes.append({'old_start': old_start, 'new_start': new_start})
    
    highlighted = []
    for i, line in enumerate(opt_lines):
        is_changed = False
        for change in changes:
            if change['new_start'] <= i + 1 <= change['new_start'] + 3:
                is_changed = True
                break
        if is_changed:
            highlighted.append("🟢 " + line)
        else:
            highlighted.append("   " + line)
    
    return '\n'.join(highlighted), changes


# ============================================================
# 核心：诊断 + 自动优化
# ============================================================

def diagnose_ai_performance(ai_name, ai_role, ai_prompt, df_results, api_key, base_url, model):
    issues = []
    strengths = []
    warnings = []
    
    for _, row in df_results.iterrows():
        speech_type = row["发言类型"]
        desc = row["发言说明"]
        feedback = row["AI点评"]
        
        if "点评" in ai_name or "评价" in ai_name:
            if not any(k in feedback for k in ["评级", "推荐", "维度", "综合"]):
                issues.append("未按格式输出（缺评级/维度/综合结构）— " + desc)
            elif "评级" not in feedback and "推荐" not in feedback[:200]:
                warnings.append("格式不完整，可能缺少评级 — " + desc)
        
        problem_types = ["观点模糊", "论据空洞", "逻辑混乱", "语言粗糙", "缺乏共情", "只说立场没理由", "跑题抓错矛盾"]
        if speech_type in problem_types:
            has_question = any(k in feedback for k in ["为什么", "补充", "具体", "理由", "说说", "哪些", "怎样", "怎么"])
            if not has_question:
                issues.append("对问题发言未追问引导 — " + desc)
            else:
                strengths.append("能主动追问引导 — " + desc)
        
        if speech_type == "跑题抓错矛盾" and "跑题" not in feedback and "方向" not in feedback:
            issues.append("对跑题发言未指出方向问题 — " + desc)
        
        if speech_type in ["完整优秀", "单维度深挖"]:
            if any(k in feedback for k in ["棒", "好", "优秀", "完整", "清楚", "突出", "亮点"]):
                strengths.append("对亮点发言肯定到位 — " + desc)
            else:
                warnings.append("对亮点发言未给予足够肯定 — " + desc)
        
        if "回应" in ai_name:
            if not any(k in feedback for k in ["你说得", "我同意", "是的", "对呀", "没错"]):
                warnings.append("回应类AI缺乏互动感 — " + desc)
        
        if "总结" in ai_name:
            if not any(k in feedback for k in ["总结", "归纳", "整理", "综合"]):
                issues.append("总结类AI未做归纳总结 — " + desc)
        
        word_count = len(feedback)
        if word_count < 20:
            warnings.append("点评过短（" + str(word_count) + "字），不够充分 — " + desc)
        elif word_count > 1000:
            warnings.append("点评过长（" + str(word_count) + "字），需要精简 — " + desc)
    
    issues = list(dict.fromkeys(issues))
    strengths = list(dict.fromkeys(strengths))
    warnings = list(dict.fromkeys(warnings))
    
    optimized_prompt = None
    
    if issues or warnings:
        issue_text = "\n".join(["- " + i for i in issues]) if issues else "无严重问题"
        warning_text = "\n".join(["- " + w for w in warnings]) if warnings else "无"
        
        optimization_request = """
【任务】优化以下AI指令词，解决诊断中发现的问题。

【原始指令词】
""" + ai_prompt + """

【AI角色】
""" + ai_role + """

【诊断出的问题】
""" + issue_text + """

【需要注意的点】
""" + warning_text + """

【优化要求】
1. 针对以上每个问题，在指令词中增加或修改对应的要求
2. 保持原有风格和语气不变
3. 只输出优化后的完整指令词，不要输出任何解释或说明
4. 确保优化后的指令词是可直接复制使用的完整版本
5. 如果问题中提到"未按格式输出"，请在指令词中明确写出输出格式模板
6. 如果问题中提到"未追问引导"，请在指令词中增加明确的追问引导要求

请输出优化后的完整指令词：
"""
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一位AI指令词优化专家。"},
                    {"role": "user", "content": optimization_request}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            optimized_prompt = response.choices[0].message.content
        except Exception as e:
            optimized_prompt = "【优化失败】" + str(e)
    
    return {
        "issues": issues,
        "strengths": strengths,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_strengths": len(strengths),
        "total_warnings": len(warnings),
        "optimized_prompt": optimized_prompt
    }


# ============================================================
# 主界面
# ============================================================

st.title("🔬 AI指令词诊断与自动优化工具 v4.0")
st.markdown("选择年级 → 上传故事脚本 → AI自动提取信息 → 生成对应年级的模拟发言 → 测试AI指令词")

with st.sidebar:
    st.header("📋 功能")
    menu = st.radio("选择操作", ["🆕 新建测试", "📚 历史记录", "📖 说明"])
    
    st.divider()
    
    st.subheader("🔑 API配置")
    api_key = st.text_input("API Key", type="password", placeholder="输入你的API Key", key="api_key_input")
    base_url = st.text_input("Base URL", value="https://api.deepseek.com", key="base_url_input")
    model = st.text_input("模型", value="deepseek-chat", key="model_input")
    
    st.caption("📁 历史记录: " + str(len(os.listdir(HISTORY_DIR))) + " 条")

if menu == "📖 说明":
    st.markdown("""
    ## 📖 使用说明（v4.0）
    
    ### 核心功能
    
    1. **选择年级**：下拉选择1-2年级 / 3年级 / 4年级 / 5年级 / 6-7年级
    2. **上传脚本**：上传本节课的故事脚本（Word或文本）
    3. **AI自动提取**：从脚本中提取人物、核心矛盾、场景、关键物品
    4. **生成模拟发言**：根据年级自动生成9种类型的模拟发言
    5. **测试AI**：用生成的发言测试你的AI指令词，自动诊断并优化
    """)

elif menu == "📚 历史记录":
    st.subheader("📚 历史测试记录")
    records = []
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(HISTORY_DIR, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                records.append({"file": filename, "course": data.get("course", "未命名"), "time": data.get("timestamp", ""), "ai_count": data.get("ai_count", 0)})
    
    if not records:
        st.info("暂无历史记录")
    else:
        for r in sorted(records, key=lambda x: x["time"], reverse=True)[:20]:
            st.caption("📅 " + r['course'] + " - " + r['time'] + " (" + str(r['ai_count']) + "个AI)")

else:
    # ---- 课程信息 ----
    col1, col2 = st.columns([1, 1])
    with col1:
        course_name = st.text_input("📚 课程名称", placeholder="如：第1课_礼物改造")
    with col2:
        grade = st.selectbox(
            "🎒 选择年级",
            options=["1-2年级", "3年级", "4年级", "5年级", "6-7年级"],
            index=0
        )
    
    grade_info = GRADE_CONFIG[grade]
    st.caption("📌 " + grade + "特征：句子长度 " + str(grade_info["sentence_len"][0]) + "-" + str(grade_info["sentence_len"][1]) + "字 | " + grade_info["features"])

    # ---- 上传故事脚本 ----
    st.subheader("📤 上传本节课的故事脚本")
    st.caption("上传Word文档（.docx）或文本文件（.txt），AI将自动提取关键信息")
    
    uploaded_file = st.file_uploader("选择文件", type=["docx", "txt"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            script_text = parse_docx(file_bytes) or ""
        else:
            script_text = file_bytes.decode("utf-8", errors="ignore")
        
        if script_text:
            st.success("✅ 文件读取成功，共 " + str(len(script_text)) + " 个字符")
            
            with st.expander("📄 查看脚本内容", expanded=False):
                st.text(script_text[:1000] + ("..." if len(script_text) > 1000 else ""))
            
            if st.button("🤖 AI自动提取关键信息", type="primary"):
                if not api_key:
                    st.error("请先在侧边栏填写API Key")
                else:
                    with st.spinner("正在分析脚本，提取关键信息..."):
                        extracted_data = extract_info_from_script(script_text, api_key, base_url, model)
                        if extracted_data:
                            st.success("✅ 提取成功！")
                            st.session_state["extracted_data"] = extracted_data
                            st.session_state["script_text"] = script_text
                        else:
                            st.error("提取失败，请检查脚本内容或重试")
        else:
            st.error("文件读取失败，请确认文件格式正确")
    
    # ---- 显示提取结果 ----
    if "extracted_data" in st.session_state:
        extracted_data = st.session_state["extracted_data"]
        st.subheader("📋 AI提取的关键信息")
        st.caption("检查以下内容是否准确，如有偏差可以手动修改")
        
        col1, col2 = st.columns(2)
        with col1:
            names_str = ", ".join(extracted_data.get("names", ["小明", "小丽", "小刚"]))
            edited_names = st.text_input("👤 人物名字", value=names_str)
            extracted_data["names"] = [n.strip() for n in edited_names.split(",") if n.strip()]
            
            conflict = extracted_data.get("conflict", "")
            edited_conflict = st.text_input("⚡ 核心矛盾", value=conflict)
            extracted_data["conflict"] = edited_conflict
        
        with col2:
            scene = extracted_data.get("scene", "")
            edited_scene = st.text_input("📍 场景", value=scene)
            extracted_data["scene"] = edited_scene
            
            items_str = ", ".join(extracted_data.get("items", ["作品", "东西"]))
            edited_items = st.text_input("📦 关键物品", value=items_str)
            extracted_data["items"] = [i.strip() for i in edited_items.split(",") if i.strip()]
        
        if st.button("✅ 确认信息，生成模拟发言"):
            st.session_state["extracted_data"] = extracted_data
            st.session_state["extracted_confirmed"] = True
            st.success("✅ 已确认，请往下滚动进行测试")
    
    # ---- AI指令词 ----
    st.subheader("🤖 输入本节课所有AI指令词")
    st.caption("每个AI用 === 分隔，第一行为AI名称")
    
    ai_configs_input = st.text_area(
        "AI指令词",
        height=200,
        placeholder="""【点评AI_温柔版】
你是一位温柔的一二年级老师，负责点评学生发言。请按照以下格式输出：
【推荐评级】xxx
【维度详评】xxx
【综合点评】xxx
===
【点评AI_严格版】
你是一位严格的一二年级老师..."""
    )
    
    # ---- 测试设置 ----
    st.subheader("📝 测试设置")
    col1, col2 = st.columns([2, 1])
    with col1:
        test_types = st.multiselect(
            "选择测试类型",
            options=[t["id"] for t in SPEECH_TYPES_CONFIG],
            format_func=lambda x: next((t["desc"] for t in SPEECH_TYPES_CONFIG if t["id"] == x), x),
            default=[t["id"] for t in SPEECH_TYPES_CONFIG]
        )
    with col2:
        samples_per_type = st.slider("每种类型生成几条", min_value=1, max_value=2, value=1)
    
    # ---- 运行 ----
    if st.button("🔬 开始诊断并自动优化", type="primary", use_container_width=True):
        if not api_key:
            st.error("请先在侧边栏填写API Key")
            st.stop()
        if not course_name:
            st.error("请填写课程名称")
            st.stop()
        if not ai_configs_input:
            st.error("请粘贴AI指令词")
            st.stop()
        if not test_types:
            st.error("请至少选择一种发言类型")
            st.stop()
        
        if "extracted_data" not in st.session_state or not st.session_state.get("extracted_confirmed", False):
            st.error("请先上传脚本并确认提取信息")
            st.stop()
        
        extracted_data = st.session_state["extracted_data"]
        
        # ---- 生成模拟发言 ----
        speeches = []
        for _ in range(samples_per_type):
            for speech_type in test_types:
                speech_text = get_speech_for_grade(grade, speech_type, extracted_data)
                speech_desc = next((t["desc"] for t in SPEECH_TYPES_CONFIG if t["id"] == speech_type), speech_type)
                speeches.append({
                    "type": speech_type,
                    "desc": speech_desc,
                    "speech": speech_text
                })
        
        st.success("✅ 已生成 " + str(len(speeches)) + " 条模拟发言（" + grade + "）")
        
        # ---- 解析AI ----
        ai_configs = parse_ai_configs(ai_configs_input)
        if not ai_configs:
            st.error("AI指令词解析失败")
            st.stop()
        
        st.success("✅ 已解析 " + str(len(ai_configs)) + " 个AI")
        for c in ai_configs:
            st.caption("  - " + c['name'] + " (" + c['role'] + ")")
        
        # ---- 执行测试 ----
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total = len(ai_configs) * len(speeches)
        idx = 0
        
        for ai_config in ai_configs:
            for speech in speeches:
                idx += 1
                status_text.text("⏳ 测试中: " + ai_config['name'] + " × " + speech['type'] + " (" + str(idx) + "/" + str(total) + ")")
                progress_bar.progress(idx / total)
                
                feedback = call_ai(api_key, base_url, model, ai_config["prompt"], speech["speech"])
                results.append({
                    "AI名称": ai_config["name"],
                    "AI角色": ai_config["role"],
                    "原始指令词": ai_config["prompt"],
                    "发言类型": speech["type"],
                    "发言说明": speech["desc"],
                    "模拟发言": speech["speech"],
                    "AI点评": feedback
                })
                time.sleep(0.2)
        
        status_text.text("✅ 测试完成！")
        progress_bar.progress(1.0)
        
        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.success("🎉 测试完成！共 " + str(len(results)) + " 条点评记录")
        
        # ---- 诊断与优化 ----
        st.subheader("📋 诊断与优化结果")
        
        all_diagnoses = []
        
        for ai_name in df["AI名称"].unique():
            ai_df = df[df["AI名称"] == ai_name]
            ai_role = ai_df["AI角色"].iloc[0]
            ai_prompt = ai_df["原始指令词"].iloc[0]
            
            with st.spinner("🔍 正在分析 " + ai_name + " 并生成优化方案..."):
                diagnosis = diagnose_ai_performance(ai_name, ai_role, ai_prompt, ai_df, api_key, base_url, model)
                all_diagnoses.append({
                    "name": ai_name,
                    "role": ai_role,
                    "original_prompt": ai_prompt,
                    "issues": diagnosis["issues"],
                    "strengths": diagnosis["strengths"],
                    "warnings": diagnosis["warnings"],
                    "total_issues": diagnosis["total_issues"],
                    "total_strengths": diagnosis["total_strengths"],
                    "total_warnings": diagnosis["total_warnings"],
                    "optimized_prompt": diagnosis["optimized_prompt"]
                })
                time.sleep(0.3)
        
        # ---- 显示结果 ----
        for diag in all_diagnoses:
            status_icon = "✅" if not diag["issues"] else "⚠️"
            with st.expander(status_icon + " " + diag['name'] + " (" + diag['role'] + ") — 问题: " + str(diag['total_issues']) + "个", expanded=True):
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔴 问题", diag["total_issues"])
                with col2:
                    st.metric("🟢 优点", diag["total_strengths"])
                with col3:
                    st.metric("🟡 提醒", diag["total_warnings"])
                
                if diag["strengths"]:
                    st.markdown("**✅ 优点：**")
                    for s in diag["strengths"]:
                        st.markdown("- " + s)
                
                if diag["issues"]:
                    st.markdown("**❌ 需要修改的问题：**")
                    for issue in diag["issues"]:
                        st.markdown("- " + issue)
                
                if diag["warnings"]:
                    st.markdown("**🟡 值得注意：**")
                    for w in diag["warnings"]:
                        st.markdown("- " + w)
                
                if diag["optimized_prompt"] and "【优化失败】" not in diag["optimized_prompt"]:
                    st.markdown("---")
                    st.markdown("**✨ AI自动优化后的指令词**")
                    st.caption("🟢 绿色行 = 新增或修改的内容")
                    
                    highlighted, changes = highlight_diff(diag["original_prompt"], diag["optimized_prompt"])
                    
                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.markdown("**📄
