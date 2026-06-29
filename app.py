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

st.set_page_config(page_title="AI指令词诊断与自动优化工具 v5.0", page_icon="🔬", layout="wide")
HISTORY_DIR = "test_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

GRADE_CONFIG = {
    "1-2年级": {"label": "1-2年级", "sentence_len": (5, 15), "features": "口语化、重复、依赖具体事例"},
    "3年级": {"label": "3年级", "sentence_len": (8, 20), "features": "连贯表达，论证较浅"},
    "4年级": {"label": "4年级", "sentence_len": (10, 25), "features": "逻辑初步清晰，有一定结构"},
    "5年级": {"label": "5年级", "sentence_len": (12, 30), "features": "观点明确，结构完整"},
    "6-7年级": {"label": "6-7年级", "sentence_len": (15, 40), "features": "表达成熟，有思辨性"}
}

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

def detect_script_type(script_text):
    if not script_text:
        return "事件型"
    topic_keywords = ["赞成", "反对", "是否", "应该", "你认为", "怎么看", "观点", "看法", "立场", "议题", "讨论"]
    for kw in topic_keywords:
        if kw in script_text:
            return "议题型"
    return "事件型"

def get_event_speech(grade, speech_type, extracted_data):
    names = extracted_data.get("names", ["小明", "小丽", "小刚"])
    items = extracted_data.get("items", ["作品", "东西"])
    if not names or not isinstance(names, list):
        names = ["小明", "小丽", "小刚"]
    if not items or not isinstance(items, list):
        items = ["作品", "东西"]
    name = random.choice(names)
    item = random.choice(items)
    templates = {
        "1-2年级": {
            "完整优秀": f"我觉得{name}应该跟对方说对不起，因为弄坏了别人的{item}是不对的。然后他可以问对方要不要帮忙修一下。",
            "观点模糊": f"我觉得他们两个都有点不对，我也不知道该怎么办，反正就是要和好吧。",
            "论据空洞": f"我觉得{name}应该赔钱，因为弄坏东西就是要赔的，我妈妈说的。",
            "逻辑混乱": f"我觉得……首先呢，{name}是男生，比较皮。然后呢，对方肯定很生气。对了，我觉得老师应该去调解。",
            "语言粗糙": f"我觉得这事吧，就{name}不对。他跑那么快干啥呀。然后对方也，东西放那儿也不对。",
            "缺乏共情": f"我觉得很简单，{name}弄坏了就要赔。按照规矩办事就行了。",
            "只说立场没理由": f"我觉得{name}应该道歉。",
            "跑题抓错矛盾": f"我觉得学校应该规定课间不能乱跑，这样就不会发生这种事了。",
            "单维度深挖": f"我觉得{name}应该先问对方'你希望我怎么做'。"
        },
        "3年级": {
            "完整优秀": f"我觉得{name}应该先真诚地向对方道歉，因为弄坏了别人的{item}就是不对。然后他可以问问对方，是想要赔钱还是想要帮忙重新做一个。",
            "观点模糊": f"我觉得这件事……嗯……应该要好好处理。反正他们两个都有点不对。",
            "论据空洞": f"我觉得{name}应该赔偿对方。因为做错了事就要负责任，我们老师也是这么说的。",
            "逻辑混乱": f"我觉得……首先呢，{name}不应该那么不小心。然后呢，对方肯定很心疼。对了，班长应该去帮忙调解。",
            "语言粗糙": f"我觉得这事吧，就是{name}不对。他跑那么快干啥呀。反正就他俩的事，好好说说就行了。",
            "缺乏共情": f"我觉得这件事很简单。{name}弄坏了就要赔，按规矩办事。",
            "只说立场没理由": f"我觉得{name}应该赔偿对方的损失。",
            "跑题抓错矛盾": f"我觉得这件事告诉我们，课间不能乱跑，学校应该管得更严一点。",
            "单维度深挖": f"我觉得{name}应该先问问对方最在意的是什么。"
        },
        "4年级": {
            "完整优秀": f"我觉得{name}应该先向对方真诚道歉，因为弄坏别人的{item}就是不对的。然后他要问清楚对方最在意什么——是花了多少钱，还是花了多少时间。然后根据对方的回答，再商量怎么弥补。",
            "观点模糊": f"我觉得这件事双方都有责任，{name}确实不小心，但对方把东西放在那里也有点不小心。",
            "论据空洞": f"我觉得{name}应该赔偿，因为损坏别人的东西就要赔偿，这是原则。",
            "逻辑混乱": f"我觉得……首先，{name}应该反省自己的行为。然后呢，对方也应该理解一下。然后……对了，我觉得老师可以帮忙调解。",
            "语言粗糙": f"我觉得{name}不对，他太不小心了。对方也很难过，东西坏了谁都心疼。但是，呃，大家各退一步就好了。",
            "缺乏共情": f"我觉得这事按规则处理就行了。{name}弄坏了，该赔多少赔多少。",
            "只说立场没理由": f"我觉得{name}应该向对方道歉并赔偿。",
            "跑题抓错矛盾": f"我觉得这件事说明学校的安全管理有问题。如果课间秩序更好一些，就不会发生这种事了。",
            "单维度深挖": f"我觉得{name}应该先了解对方真正的感受和需求。每个人对'失去'的反应不同。"
        },
        "5年级": {
            "完整优秀": f"我认为这件事的核心不是赔偿问题，而是{name}能否真诚面对自己的错误。首先，{name}应该主动道歉，要表达自己理解对方的感受。其次，要了解对方最希望得到什么样的弥补。最后，双方一起商量出都能接受的方案。",
            "观点模糊": f"我觉得这件事双方都有一定的责任吧。{name}确实不小心，但对方把东西放在那个位置也不太安全。具体怎么解决，我也说不太清楚。",
            "论据空洞": f"我觉得{name}必须赔偿，因为损坏别人的东西就要赔偿。这是基本的规则和道德要求。",
            "逻辑混乱": f"关于这件事，我有几个想法。第一，{name}应该道歉。第二，对方也有责任。第三，老师应该参与调解。反正就是这些吧。",
            "语言粗糙": f"我觉得{name}这事做得不对，他太不小心了。然后对方呢，东西被弄坏了肯定会生气。反正就是各退一步。",
            "缺乏共情": f"我认为这是一个简单的责任认定问题。{name}的行为造成了损害，就应该承担相应责任。",
            "只说立场没理由": f"我认为{name}应当为自己的行为负责，向对方道歉并做出相应赔偿。",
            "跑题抓错矛盾": f"我觉得这件事暴露出学校管理的一个漏洞。如果学校有更完善的安全制度，类似事件就能避免。",
            "单维度深挖": f"我认为这个问题的关键在'换位思考'。{name}需要真正站在对方的立场去感受。"
        },
        "6-7年级": {
            "完整优秀": f"我认为这件事的核心不是简单的赔偿问题，而是关乎责任认知与人际修复的深层议题。首先，{name}需要完成一次真诚的自我反思。其次，双方需要开放地沟通各自的需求与期待。最后，共同制定一个具体的、可执行的修复方案。",
            "观点模糊": f"我觉得这件事要从多个角度来看。一方面，{name}确实有不小心的责任；另一方面，对方把东西放在那里也有一定风险。",
            "论据空洞": f"我认为{name}应该承担赔偿责任。因为从基本的社会规则来看，造成他人损失就需要补偿。",
            "逻辑混乱": f"我想从几个层面来分析这件事。首先，关于责任归属……嗯，{name}确实有过失。其次，关于解决方式……可能需要道歉和赔偿。",
            "语言粗糙": f"我觉得{name}肯定要道歉啊，这事就是他不对。他太不小心了，把别人辛辛苦苦做的东西弄坏了。",
            "缺乏共情": f"我认为这是一个典型的责任认定案例。从行为结果来看，{name}造成了损害；从因果关系来看，损害与行为直接相关。",
            "只说立场没理由": f"我认为{name}应当为自己的过失行为承担全部责任，包括诚恳道歉和物质赔偿。",
            "跑题抓错矛盾": f"这件事让我思考的是学校在冲突调解机制上的不足。我们应该把注意力放在制度建设上。",
            "单维度深挖": f"我认为这个案例最值得深思的是'同理心'在冲突解决中的核心作用。"
        }
    }
    grade_templates = templates.get(grade, templates["3年级"])
    result = grade_templates.get(speech_type, "发言内容待生成")
    return result if result else "发言内容待生成"

def get_topic_speech(grade, speech_type, extracted_data):
    topic = extracted_data.get("topic", "这个议题")
    names = extracted_data.get("names", ["小明", "小丽", "小刚"])
    if not names or not isinstance(names, list):
        names = ["小明", "小丽", "小刚"]
    name = random.choice(names)
    templates = {
        "1-2年级": {
            "完整优秀": f"我觉得应该{topic}，因为这样做会让大家都更方便。我也想问一下别人的想法。",
            "观点模糊": f"我觉得这个……我也不知道该怎么办，好像这样也行，那样也行。",
            "论据空洞": f"我觉得应该{topic}，因为我妈妈也是这样说的。",
            "逻辑混乱": f"我觉得……首先呢，应该{topic}。然后呢，这样比较好。对了，我还想到一个问题……算了，就这样吧。",
            "语言粗糙": f"我觉得应该{topic}，就这样吧，挺好的。",
            "缺乏共情": f"我觉得应该{topic}。规则就是这样的，不用想太多。",
            "只说立场没理由": f"我觉得应该{topic}。",
            "跑题抓错矛盾": f"我觉得这个问题不重要，我们应该关注别的事情。",
            "单维度深挖": f"我觉得应该{topic}，因为每个人都有自己的想法，我们应该互相理解。"
        },
        "3年级": {
            "完整优秀": f"我觉得应该{topic}，因为这样做对大家都有好处。我也想知道别人是怎么想的。",
            "观点模糊": f"我觉得这个问题……嗯……好像两边都有道理，我也不太确定。",
            "论据空洞": f"我觉得应该{topic}，因为老师说这样做是对的。",
            "逻辑混乱": f"我觉得……首先，应该{topic}。然后，这样比较好。对了，我还想到……反正就是这样。",
            "语言粗糙": f"我觉得应该{topic}，就这个意思，大家都懂的。",
            "缺乏共情": f"我觉得应该{topic}。事情就是这样，按规矩办就行了。",
            "只说立场没理由": f"我觉得应该{topic}。",
            "跑题抓错矛盾": f"我觉得这个问题不重要，我们应该想点别的。",
            "单维度深挖": f"我觉得应该{topic}，因为每个人都有自己的立场，我们需要互相理解。"
        },
        "4年级": {
            "完整优秀": f"我认为应该{topic}，因为这样做更合理。首先，这符合大多数人的利益；其次，这样做也能照顾到少数人的感受。我想听听大家的看法。",
            "观点模糊": f"我觉得这件事两方面都有道理，很难说哪个更好。可能要看具体情况吧。",
            "论据空洞": f"我认为应该{topic}，因为这是正确的选择。大家都这么说，应该没错。",
            "逻辑混乱": f"我觉得……首先，应该{topic}。然后呢，这样会更好。哦对了，我还想到一个问题……反正就是这样的。",
            "语言粗糙": f"我觉得应该{topic}，就这样，不用搞那么复杂。",
            "缺乏共情": f"我认为应该{topic}。这是一个理性的选择，不需要考虑太多情感因素。",
            "只说立场没理由": f"我认为应该{topic}。",
            "跑题抓错矛盾": f"我觉得这个问题本身就有问题，我们应该讨论更重要的议题。",
            "单维度深挖": f"我认为应该{topic}，因为每个人都有自己的立场和理由，我们需要找到大家都能接受的方案。"
        },
        "5年级": {
            "完整优秀": f"我认为应该{topic}，因为这样做能带来更大的社会价值。首先，它能促进整体的发展；其次，它也能考虑到个体的需求。当然，在实施过程中需要注意平衡各方利益。",
            "观点模糊": f"我觉得这个问题很复杂，从不同角度看有不同的理解。可能没有一个绝对正确的答案。",
            "论据空洞": f"我认为应该{topic}，因为这显然是正确的选择。理由很简单，就是这样做对大家都好。",
            "逻辑混乱": f"关于这个问题，我有几个想法。第一，应该{topic}。第二，这样比较合理。第三，还需要考虑其他因素。反正就是这些吧。",
            "语言粗糙": f"我觉得应该{topic}，这个大家都明白，不用多说。",
            "缺乏共情": f"我认为应该{topic}。这是一个效率优先的选择，不需要过多考虑情感因素。",
            "只说立场没理由": f"我认为应该{topic}。这是合理的决策。",
            "跑题抓错矛盾": f"我觉得这个议题本身的价值不大，我们应该关注更有建设性的方向。",
            "单维度深挖": f"我认为应该{topic}，因为每个人都有自己的立场和价值观。真正的问题在于我们如何找到平衡点。"
        },
        "6-7年级": {
            "完整优秀": f"我认为应该{topic}，因为这是符合社会发展方向的理性选择。首先，它能提升整体效率；其次，它也能保障个体的基本权益。当然，在实施过程中需要建立完善的配套机制。我想强调的是，任何决策都需要在利弊之间找到平衡。",
            "观点模糊": f"我认为这个问题需要从多个维度来分析。从不同的立场出发，可能会得出不同的结论。这本身就是一个值得深入探讨的议题。",
            "论据空洞": f"我认为应该{topic}，因为这是显而易见的正确选择。理由就是这样做符合常识和逻辑。",
            "逻辑混乱": f"我想从几个层面来思考这个问题。首先，应该{topic}。其次，这符合发展趋势。再者，还需要考虑……嗯，总之就是这样。",
            "语言粗糙": f"我觉得应该{topic}，这个没什么好讨论的，就是这样。",
            "缺乏共情": f"我认为应该{topic}。这是一个基于效率和理性的决策，情感因素不应成为主要考量。",
            "只说立场没理由": f"我认为应该{topic}。这是经过理性判断后的选择。",
            "跑题抓错矛盾": f"我认为这个议题背后的核心问题其实是价值取向的差异，而不是表面的选择。我们需要重新审视问题的本质。",
            "单维度深挖": f"我认为应该{topic}，因为这个选择背后涉及的是不同价值观的碰撞。我们需要的不是简单的非此即彼，而是更深层次的对话与理解。"
        }
    }
    grade_templates = templates.get(grade, templates["3年级"])
    result = grade_templates.get(speech_type, "发言内容待生成")
    return result if result else "发言内容待生成"

def get_speech_for_grade(grade, speech_type, extracted_data, script_type):
    if script_type == "议题型":
        return get_topic_speech(grade, speech_type, extracted_data)
    else:
        return get_event_speech(grade, speech_type, extracted_data)

def parse_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text
    except Exception as e:
        return None

def extract_info_from_script(script_text, api_key, base_url, model, script_type):
    if not script_text or len(script_text.strip()) < 10:
        return None
    if script_type == "议题型":
        prompt = "你是一位教育内容分析专家。请从下面的议题讨论脚本中提取核心议题、人物名字、可能的观点。严格按JSON格式输出：{\"topic\": \"核心议题\", \"names\": [\"名字1\", \"名字2\"], \"viewpoints\": [\"观点1\", \"观点2\"]}\n\n脚本内容：\n" + script_text[:2000]
    else:
        prompt = "你是一位教育内容分析专家。请从下面的故事脚本中提取人物名字、核心矛盾、场景、关键物品。严格按JSON格式输出：{\"names\": [\"名字1\", \"名字2\"], \"conflict\": \"核心矛盾\", \"scene\": \"场景\", \"items\": [\"物品1\", \"物品2\"]}\n\n脚本内容：\n" + script_text[:2000]
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "请严格按照JSON格式输出。"}, {"role": "user", "content": prompt}], temperature=0.3, max_tokens=800)
        content = response.choices[0].message.content
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        return None

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
        response = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_speech}], temperature=0.7, max_tokens=2000)
        return response.choices[0].message.content
    except Exception as e:
        return "调用失败: " + str(e)

def highlight_diff(original, optimized):
    if not optimized or not original:
        return optimized, []
    orig_lines = original.split('\n')
    opt_lines = optimized.split('\n')
    diff = list(difflib.unified_diff(orig_lines, opt_lines, fromfile='原始', tofile='优化后', lineterm=''))
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
        optimization_request = "【任务】优化以下AI指令词，解决诊断中发现的问题。\n\n【原始指令词】\n" + ai_prompt + "\n\n【AI角色】\n" + ai_role + "\n\n【诊断出的问题】\n" + issue_text + "\n\n【需要注意的点】\n" + warning_text + "\n\n【优化要求】\n1. 针对以上每个问题，在指令词中增加或修改对应的要求\n2. 保持原有风格和语气不变\n3. 只输出优化后的完整指令词，不要输出任何解释或说明\n4. 确保优化后的指令词是可直接复制使用的完整版本\n5. 如果问题中提到'未按格式输出'，请在指令词中明确写出输出格式模板\n6. 如果问题中提到'未追问引导'，请在指令词中增加明确的追问引导要求\n\n请输出优化后的完整指令词："
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "你是一位AI指令词优化专家。"}, {"role": "user", "content": optimization_request}], temperature=0.5, max_tokens=2000)
            optimized_prompt = response.choices[0].message.content
        except Exception as e:
            optimized_prompt = "优化失败: " + str(e)
    return {"issues": issues, "strengths": strengths, "warnings": warnings, "total_issues": len(issues), "total_strengths": len(strengths), "total_warnings": len(warnings), "optimized_prompt": optimized_prompt}

st.title("🔬 AI指令词诊断与自动优化工具 v5.0")
st.markdown("选择年级 → 上传故事脚本 → 自动识别脚本类型 → 生成模拟发言 → 测试AI指令词")

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
    ## 📖 使用说明（v5.0）
    ### 🆕 新功能：双模式支持
    工具会自动识别脚本类型：
    | 脚本类型 | 适用场景 | 示例 |
    |---------|---------|------|
    | **事件型** | 有情节、有冲突的故事 | 《不能没有礼物的日子》 |
    | **议题型** | 需要表达观点和理由的讨论 | 《你赞成拆除城市的旧建筑吗？》 |
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
    col1, col2 = st.columns([1, 1])
    with col1:
        course_name = st.text_input("📚 课程名称", placeholder="如：第1课_礼物改造")
    with col2:
        grade = st.selectbox("🎒 选择年级", options=["1-2年级", "3年级", "4年级", "5年级", "6-7年级"], index=0)
    grade_info = GRADE_CONFIG[grade]
    st.caption("📌 " + grade + "特征：句子长度 " + str(grade_info["sentence_len"][0]) + "-" + str(grade_info["sentence_len"][1]) + "字 | " + grade_info["features"])
    st.subheader("📤 上传本节课的故事脚本")
    st.caption("上传Word文档（.docx）或文本文件（.txt），AI将自动识别脚本类型并提取关键信息")
    uploaded_file = st.file_uploader("选择文件", type=["docx", "txt"], label_visibility="collapsed")
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            script_text = parse_docx(file_bytes) or ""
        else:
            script_text = file_bytes.decode("utf-8", errors="ignore")
        if script_text:
            st.success("✅ 文件读取成功，共 " + str(len(script_text)) + " 个字符")
            detected_type = detect_script_type(script_text)
            st.info("📌 自动识别脚本类型：**" + detected_type + "**")
            script_type = st.radio("确认或手动选择脚本类型：", options=["事件型", "议题型"], index=0 if detected_type == "事件型" else 1, horizontal=True)
            with st.expander("📄 查看脚本内容", expanded=False):
                st.text(script_text[:1000] + ("..." if len(script_text) > 1000 else ""))
            if st.button("🤖 AI自动提取关键信息", type="primary"):
                if not api_key:
                    st.error("请先在侧边栏填写API Key")
                else:
                    with st.spinner("正在分析脚本，提取关键信息..."):
                        extracted_data = extract_info_from_script(script_text, api_key, base_url, model, script_type)
                        if extracted_data:
                            st.success("✅ 提取成功！")
                            st.session_state["extracted_data"] = extracted_data
                            st.session_state["script_text"] = script_text
                            st.session_state["script_type"] = script_type
                        else:
                            st.error("提取失败，请检查脚本内容或重试")
        else:
            st.error("文件读取失败，请确认文件格式正确")
    if "extracted_data" in st.session_state:
        extracted_data = st.session_state["extracted_data"]
        script_type = st.session_state.get("script_type", "事件型")
        st.subheader("📋 AI提取的关键信息")
        st.caption("检查以下内容是否准确，如有偏差可以手动修改")
        if "names" not in extracted_data or not isinstance(extracted_data["names"], list):
            extracted_data["names"] = ["小明", "小丽", "小刚"]
        col1, col2 = st.columns(2)
        with col1:
            names_str = ", ".join(extracted_data.get("names", ["小明", "小丽", "小刚"]))
            edited_names = st.text_input("👤 人物名字", value=names_str)
            extracted_data["names"] = [n.strip() for n in edited_names.split(",") if n.strip()]
            if not extracted_data["names"]:
                extracted_data["names"] = ["小明", "小丽", "小刚"]
            if script_type == "事件型":
                conflict = extracted_data.get("conflict", "")
                edited_conflict = st.text_input("⚡ 核心矛盾", value=conflict)
                extracted_data["conflict"] = edited_conflict
            else:
                topic = extracted_data.get("topic", "")
                edited_topic = st.text_input("💡 核心议题", value=topic)
                extracted_data["topic"] = edited_topic
        with col2:
            if script_type == "事件型":
                scene = extracted_data.get("scene", "")
                edited_scene = st.text_input("📍 场景", value=scene)
                extracted_data["scene"] = edited_scene
                items_str = ", ".join(extracted_data.get("items", ["作品", "东西"]))
                edited_items = st.text_input("📦 关键物品", value=items_str)
                extracted_data["items"] = [i.strip() for i in edited_items.split(",") if i.strip()]
                if not extracted_data["items"]:
                    extracted_data["items"] = ["作品", "东西"]
            else:
                viewpoints_str = ", ".join(extracted_data.get("viewpoints", ["观点1", "观点2"]))
                edited_viewpoints = st.text_input("💬 可能的观点", value=viewpoints_str)
                extracted_data["viewpoints"] = [v.strip() for v in edited_viewpoints.split(",") if v.strip()]
                if not extracted_data["viewpoints"]:
                    extracted_data["viewpoints"] = ["赞成", "反对"]
        if st.button("✅ 确认信息，生成模拟发言"):
            st.session_state["extracted_data"] = extracted_data
            st.session_state["extracted_confirmed"] = True
            st.success("✅ 已确认，请往下滚动进行测试")
    st.subheader("🤖 输入本节课所有AI指令词")
    st.caption("每个AI用 === 分隔，第一行为AI名称")
    ai_configs_input = st.text_area("AI指令词", height=200, placeholder="【点评AI_温柔版】\n你是一位温柔的一二年级老师...\n===\n【点评AI_严格版】\n你是一位严格的一二年级老师...")
    st.subheader("📝 测试设置")
    col1, col2 = st.columns([2, 1])
    with col1:
        test_types = st.multiselect("选择测试类型", options=[t["id"] for t in SPEECH_TYPES_CONFIG], format_func=lambda x: next((t["desc"] for t in SPEECH_TYPES_CONFIG if t["id"] == x), x), default=[t["id"] for t in SPEECH_TYPES_CONFIG])
    with col2:
        samples_per_type = st.slider("每种类型生成几条", min_value=1, max_value=2, value=1)
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
        extracted_data = st.session_state["extracted_data
