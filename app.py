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

st.set_page_config(page_title="AI指令词诊断与自动优化工具 v5.2", page_icon="🔬", layout="wide")
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
    {"id": "完整优秀", "desc": "✅ 完整发言（观点明确+理由充分+结构完整+表达流畅+有人文关怀）"},
    {"id": "观点模糊", "desc": "⚠️ 观点模糊，没有抓住核心问题"},
    {"id": "论据空洞", "desc": "⚠️ 观点明确但论据不足，说不出理由"},
    {"id": "逻辑混乱", "desc": "⚠️ 逻辑不清，思路跳跃，结构混乱"},
    {"id": "语言粗糙", "desc": "⚠️ 语言表达有问题，用词不准"},
    {"id": "缺乏共情", "desc": "⚠️ 只讲道理，缺少对人的关心和理解"},
    {"id": "只说立场没理由", "desc": "⚠️ 只说立场，没有论证"},
    {"id": "跑题抓错矛盾", "desc": "⚠️ 回答偏离了核心问题"},
    {"id": "单维度深挖", "desc": "✅ 从一个角度深入，有亮点但不够全面"}
]

def detect_script_type(script_text):
    if not script_text:
        return "事件型"
    topic_keywords = ["赞成", "反对", "是否", "应该", "你认为", "怎么看", "观点", "看法", "立场", "议题", "讨论", "价值"]
    for kw in topic_keywords:
        if kw in script_text:
            return "议题型"
    return "事件型"

def get_event_speech(grade, speech_type, extracted_data):
    """事件型：围绕核心问题生成模拟发言"""
    names = extracted_data.get("names", ["小明", "小丽", "小刚"])
    question = extracted_data.get("question", "你有什么特点？")
    if not names or not isinstance(names, list):
        names = ["小明", "小丽", "小刚"]
    name = random.choice(names)
    
    templates = {
        "1-2年级": {
            "完整优秀": f"我觉得{name}有特点，{question}我来说说吧。我觉得自己有点不一样的地方，就是遇到事情会想一想怎么做。我觉得这个特点适合当小班长，因为小班长要帮老师做事，想一想才能把事情做好。",
            "观点模糊": f"嗯……{question}我好像也没什么特别的特点吧，就是普通的孩子。特点变优点？我也不知道。",
            "论据空洞": f"我觉得我的特点是跑得快，跑得快就是优点啊，没什么好说的。",
            "逻辑混乱": f"我觉得……我的特点是？哦对了，我画画好。然后呢……画画好的人可以当画家？还是当别的？反正就是好吧。",
            "语言粗糙": f"我特点就是爱玩，玩好了就心情好。问题啥的，不懂。",
            "缺乏共情": f"我觉得特点就是特点，不用管别人怎么想。反正我觉得自己挺好的。",
            "只说立场没理由": f"我觉得我的特点是跑得快。",
            "跑题抓错矛盾": f"我觉得这个问题不重要，我们应该想想课间吃什么。",
            "单维度深挖": f"我觉得我的特点是很爱观察。上次在操场上，我发现了别人没注意到的东西。我觉得爱观察的人，以后可以当科学家，因为科学家就是要观察。"
        },
        "3年级": {
            "完整优秀": f"我觉得{name}有特点，{question}我想说，我的特点是比较细心。上次大家都没发现的问题，我发现了。我觉得这个特点适合当小组长，因为小组长要检查作业，细心的人才能检查好。",
            "观点模糊": f"这个问题……嗯……好像每个人都有自己的特点吧。我也不知道我有什么特点，反正就是普通的小朋友。",
            "论据空洞": f"我觉得我的特点是跑得快，跑得快就是优点。老师也说过跑得快好。",
            "逻辑混乱": f"我觉得……首先，我的特点是画画好。然后呢，画画好的人可以当画家。哦对了，也可以当设计师。反正画画好就是好。",
            "语言粗糙": f"我特点就是爱说话，说话能让别人开心。这个问题就这样吧。",
            "缺乏共情": f"特点就是特点，不用管别人怎么看。自己觉得好就行了。",
            "只说立场没理由": f"我觉得我的特点是安静。",
            "跑题抓错矛盾": f"我觉得这个问题不重要，我们应该聊聊别的事情。",
            "单维度深挖": f"我觉得我的特点是特别爱帮助别人。上次同学忘记带笔，我借给他了。我觉得爱帮助人的人，可以当志愿者，因为志愿者就是帮助别人。"
        },
        "4年级": {
            "完整优秀": f"我觉得{name}有特点，{question}我觉得我的特点是很会观察。比如上次科学课，我发现了别人没注意到的细节。我觉得这个特点适合当科学家，因为科学家就是要仔细观察才能发现秘密。当然，这个特点在写作文的时候也很有用。",
            "观点模糊": f"这个问题好像有点难回答。每个人都有自己的特点吧，但我不知道我的特点是什么，可能还要再想想。",
            "论据空洞": f"我觉得我的特点是认真，认真就是优点。老师经常表扬认真的人。",
            "逻辑混乱": f"我觉得我的特点是……嗯，比较有耐心。然后有耐心的人适合当老师？还是当医生？我觉得都可以吧，反正就是有耐心。",
            "语言粗糙": f"我特点就是爱打篮球，打篮球很厉害。这个问题还有什么好说的。",
            "缺乏共情": f"我觉得特点就是自己的事，不用考虑别人怎么想。自己觉得好就行。",
            "只说立场没理由": f"我觉得我的特点是画画好。",
            "跑题抓错矛盾": f"我觉得这个问题意义不大，我们应该讨论更有实际意义的话题。",
            "单维度深挖": f"我觉得我的特点是有耐心。上次做手工，我花了很长时间完成了，别人都放弃了。我觉得有耐心的人，以后可以当老师，因为老师要一遍一遍教学生，没有耐心不行。"
        },
        "5年级": {
            "完整优秀": f"我觉得{name}有特点，{question}我认为我的特点是比较善于倾听。在小组讨论时，我会先听别人说完再表达自己的看法。我觉得这个特点适合当调解员，因为调解员需要先理解双方的想法，才能帮助解决问题。",
            "观点模糊": f"每个人都有自己的特点，这个我同意。但具体是什么特点，在不同的场景下表现可能不一样。所以很难说哪个特点是最好的。",
            "论据空洞": f"我觉得我的特点是诚实，诚实是一种美德，所以一定是优点。不需要更多的理由。",
            "逻辑混乱": f"关于这个问题，我有几个想法。第一，我觉得我的特点是有责任心。第二，有责任心的人适合当班干部。第三，但是我有时候也会忘记带作业。所以……好像也不一定。",
            "语言粗糙": f"我觉得我的特点就是靠谱，答应的事情会做到。这个特点挺好的，就是这样。",
            "缺乏共情": f"我认为特点的价值在于它本身，而不在于别人怎么评价。重要的是自己认可自己。",
            "只说立场没理由": f"我认为我的特点是责任心强。",
            "跑题抓错矛盾": f"我觉得这个问题本身就不太对。特点能不能变成优点，要看别人怎么看待，不是一个简单的是非问题。",
            "单维度深挖": f"我认为我的特点是同理心比较强。上次同桌因为没考好很难过，我能感受到她的心情。我觉得有同理心的人，以后可以当心理咨询师或者医生，因为能理解病人的感受是很重要的。"
        },
        "6-7年级": {
            "完整优秀": f"我觉得{name}有特点，{question}我认为我的特点是批判性思维。我不太容易轻信一个观点，会自己想一想是不是有道理。比如在讨论中，我会先分析对方说的有没有漏洞，再形成自己的看法。我觉得这个特点适合从事法律或研究类的工作，因为这类工作需要独立判断和深度分析。当然，在团队合作中，我也需要学会更好地表达自己的观点。",
            "观点模糊": f"这个问题触及了一个本质问题：如何定义'特点'。在不同的语境下，同样的特质可能表现为优点或缺点。所以我认为，这个问题没有标准答案。",
            "论据空洞": f"我认为我的特点是勤奋。勤奋就是最大的优点，不需要解释。任何成功都离不开勤奋。",
            "逻辑混乱": f"关于这个问题，我想从几个方面来思考。首先，勤奋是关键。其次，沟通能力也很重要。再者，思维方式也会影响。嗯……总之这些都很重要。",
            "语言粗糙": f"我觉得我的特点就是靠谱，答应的事情一定会做到。这个特点我觉得挺好的，反正就是靠谱。",
            "缺乏共情": f"我认为特点本身是中性的，它的价值在于被用在什么地方。这是一种理性的、效率导向的视角。",
            "只说立场没理由": f"我认为我的特点是批判性思维和分析能力。",
            "跑题抓错矛盾": f"我认为讨论'特点变优点'这个命题，本质上是探讨社会评价标准的问题。我们要被社会评价标准所定义吗？这才是我更关心的问题。",
            "单维度深挖": f"我认为我的特点是比较强的自我反思能力。我经常会复盘自己做得不好的地方，然后想下次怎么改进。我觉得这个特点在几乎任何领域都能成为优点，因为反思能力能让一个人持续成长。不过，我也需要注意不要过度反思，避免陷入自我怀疑。"
        }
    }
    grade_templates = templates.get(grade, templates["3年级"])
    result = grade_templates.get(speech_type, "发言内容待生成")
    return result if result else "发言内容待生成"

def get_topic_speech(grade, speech_type, extracted_data):
    """议题型：围绕核心议题生成模拟发言"""
    names = extracted_data.get("names", ["小明", "小丽", "小刚"])
    question = extracted_data.get("question", "这个议题")
    if not names or not isinstance(names, list):
        names = ["小明", "小丽", "小刚"]
    name = random.choice(names)
    
    templates = {
        "1-2年级": {
            "完整优秀": f"我觉得{name}有想法。{question}我说说我的看法。我觉得应该这样做，因为这样做对大家都好。我也想知道别人是怎么想的。",
            "观点模糊": f"我觉得这个问题……我也不知道，好像这样也行，那样也行。",
            "论据空洞": f"我觉得应该这样，因为我妈妈也是这样说的。",
            "逻辑混乱": f"我觉得……首先呢，应该这样。然后呢，这样比较好。算了，就这样吧。",
            "语言粗糙": f"我觉得应该这样，挺好的。",
            "缺乏共情": f"我觉得应该这样。规则就是这样的，不用想太多。",
            "只说立场没理由": f"我觉得应该这样。",
            "跑题抓错矛盾": f"我觉得这个问题不重要，我们应该关注别的事情。",
            "单维度深挖": f"我觉得应该这样，因为每个人都有自己的想法，我们应该互相理解。"
        },
        "3年级": {
            "完整优秀": f"我觉得{name}有想法。{question}我认为应该这样做，因为这样做对大家都有好处。我也想知道别人是怎么想的。",
            "观点模糊": f"我觉得这个问题……嗯……好像两边都有道理，我也不太确定。",
            "论据空洞": f"我觉得应该这样，因为老师说这样做是对的。",
            "逻辑混乱": f"我觉得……首先，应该这样。然后，这样比较好。反正就是这样。",
            "语言粗糙": f"我觉得应该这样，就这个意思。",
            "缺乏共情": f"我觉得应该这样。事情就是这样，按规矩办就行了。",
            "只说立场没理由": f"我觉得应该这样。",
            "跑题抓错矛盾": f"我觉得这个问题不重要，我们应该想点别的。",
            "单维度深挖": f"我觉得应该这样，因为每个人都有自己的立场，我们需要互相理解。"
        },
        "4年级": {
            "完整优秀": f"我觉得{name}有想法。{question}我认为应该这样做，因为这样做更合理。首先，这符合大多数人的利益；其次，这样做也能照顾到少数人的感受。我想听听大家的看法。",
            "观点模糊": f"我觉得这件事两方面都有道理，很难说哪个更好。可能要看具体情况吧。",
            "论据空洞": f"我认为应该这样做，因为这是正确的选择。大家都这么说，应该没错。",
            "逻辑混乱": f"我觉得……首先，应该这样。然后呢，这样会更好。哦对了，我还想到一个问题……反正就是这样的。",
            "语言粗糙": f"我觉得应该这样，就这样，不用搞那么复杂。",
            "缺乏共情": f"我认为应该这样做。这是一个理性的选择，不需要考虑太多情感因素。",
            "只说立场没理由": f"我认为应该这样做。",
            "跑题抓错矛盾": f"我觉得这个问题本身就有问题，我们应该讨论更重要的议题。",
            "单维度深挖": f"我认为应该这样做，因为每个人都有自己的立场和理由，我们需要找到大家都能接受的方案。"
        },
        "5年级": {
            "完整优秀": f"我觉得{name}有想法。{question}我认为应该这样做，因为这样做能带来更大的价值。首先，它能促进整体的发展；其次，它也能考虑到个体的需求。当然，在实施过程中需要注意平衡各方利益。",
            "观点模糊": f"我觉得这个问题很复杂，从不同角度看有不同的理解。可能没有一个绝对正确的答案。",
            "论据空洞": f"我认为应该这样做，因为这显然是正确的选择。理由很简单，就是这样做对大家都好。",
            "逻辑混乱": f"关于这个问题，我有几个想法。第一，应该这样。第二，这样比较合理。第三，还需要考虑其他因素。反正就是这些吧。",
            "语言粗糙": f"我觉得应该这样，这个大家都明白，不用多说。",
            "缺乏共情": f"我认为应该这样做。这是一个效率优先的选择，不需要过多考虑情感因素。",
            "只说立场没理由": f"我认为应该这样做。这是合理的决策。",
            "跑题抓错矛盾": f"我觉得这个议题本身的价值不大，我们应该关注更有建设性的方向。",
            "单维度深挖": f"我认为应该这样做，因为每个人都有自己的立场和价值观。真正的问题在于我们如何找到平衡点。"
        },
        "6-7年级": {
            "完整优秀": f"我觉得{name}有想法。{question}我认为应该这样做，因为这是符合社会发展方向的理性选择。首先，它能提升整体效率；其次，它也能保障个体的基本权益。当然，在实施过程中需要建立完善的配套机制。我想强调的是，任何决策都需要在利弊之间找到平衡。",
            "观点模糊": f"我认为这个问题需要从多个维度来分析。从不同的立场出发，可能会得出不同的结论。这本身就是一个值得深入探讨的议题。",
            "论据空洞": f"我认为应该这样做，因为这是显而易见的正确选择。理由就是这样做符合常识和逻辑。",
            "逻辑混乱": f"我想从几个层面来思考这个问题。首先，应该这样。其次，这符合发展趋势。再者，还需要考虑……嗯，总之就是这样。",
            "语言粗糙": f"我觉得应该这样，这个没什么好讨论的。",
            "缺乏共情": f"我认为应该这样做。这是一个基于效率和理性的决策，情感因素不应成为主要考量。",
            "只说立场没理由": f"我认为应该这样做。这是经过理性判断后的选择。",
            "跑题抓错矛盾": f"我认为这个议题背后的核心问题其实是价值取向的差异，而不是表面的选择。我们需要重新审视问题的本质。",
            "单维度深挖": f"我认为应该这样做，因为这个选择背后涉及的是不同价值观的碰撞。我们需要的不是简单的非此即彼，而是更深层次的对话与理解。"
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
    """提取脚本关键信息，支持长文本（最多8000字符）"""
    if not script_text or len(script_text.strip()) < 10:
        return None
    
    # 提取前8000字符（足够覆盖完整脚本）
    max_chars = 8000
    truncated_text = script_text[:max_chars]
    if len(script_text) > max_chars:
        truncated_text += "\n\n...（脚本较长，已截取前8000字符）"
    
    if script_type == "议题型":
        prompt = f"""你是一位教育内容分析专家。请从下面的议题讨论脚本中提取以下关键信息，严格按JSON格式输出：

{{
  "names": ["人物名字1", "人物名字2", "人物名字3"],
  "question": "脚本中直接问读者/学生的问题是什么？原话摘录。如果有多个问题，全部合并列出。",
  "viewpoints": ["观点1", "观点2"]
}}

脚本内容：
{truncated_text}"""
    else:
        prompt = f"""你是一位教育内容分析专家。请从下面的故事脚本中提取以下关键信息，严格按JSON格式输出：

{{
  "names": ["人物名字1", "人物名字2", "人物名字3"],
  "question": "脚本中直接问读者/学生的问题是什么？原话摘录。如果有多个问题（如多轮对话、单轮对话中的问题），请全部提取合并。",
  "conflict": "核心矛盾一句话概括",
  "scene": "主要场景",
  "items": ["物品1", "物品2"]
}}

脚本内容：
{truncated_text}"""
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位教育内容分析专家。请仔细阅读脚本全文，提取所有直接问读者/学生的问题。严格按照JSON格式输出，不要添加任何其他内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
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
        optimization_request = """【任务】优化以下AI指令词，解决诊断中发现的问题。

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

请输出优化后的完整指令词："""
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
            optimized_prompt = "优化失败: " + str(e)
    return {"issues": issues, "strengths": strengths, "warnings": warnings, "total_issues": len(issues), "total_strengths": len(strengths), "total_warnings": len(warnings), "optimized_prompt": optimized_prompt}

st.title("🔬 AI指令词诊断与自动优化工具 v5.2")
st.markdown("选择年级 → 上传故事脚本 → 自动提取核心问题 → 生成围绕问题的模拟发言 → 测试AI指令词")

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
    st.markdown("""## 📖 使用说明（v5.2）
    
    ### 🆕 升级：支持长脚本提取
    
    v5.2 将脚本读取上限从 2000 字符提升到 **8000 字符**，能够完整读取包含对话表格的完整剧本。
    
    ### 核心功能
    1. **选择年级**：1-2年级 / 3年级 / 4年级 / 5年级 / 6-7年级
    2. **上传脚本**：上传本节课的故事脚本（Word或文本），最长支持8000字符
    3. **自动提取**：提取人物、核心矛盾、场景、**核心问题**
    4. **确认问题**：检查提取的问题是否正确，可以手动修改
    5. **生成模拟发言**：围绕核心问题生成9种模拟发言
    6. **测试AI**：用生成的发言测试你的AI指令词，自动诊断并优化
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
    st.caption("上传Word文档（.docx）或文本文件（.txt），最长支持8000字符，AI将自动提取关键信息")
    uploaded_file = st.file_uploader("选择文件", type=["docx", "txt"], label_visibility="collapsed")
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            script_text = parse_docx(file_bytes) or ""
        else:
            script_text = file_bytes.decode("utf-8", errors="ignore")
        if script_text:
            char_count = len(script_text)
            st.success("✅ 文件读取成功，共 " + str(char_count) + " 个字符" + ("（已超出8000字符限制，将截取前8000字符）" if char_count > 8000 else ""))
            detected_type = detect_script_type(script_text)
            st.info("📌 自动识别脚本类型：**" + detected_type + "**")
            script_type = st.radio("确认或手动选择脚本类型：", options=["事件型", "议题型"], index=0 if detected_type == "事件型" else 1, horizontal=True)
            with st.expander("📄 查看脚本内容（前1000字符）", expanded=False):
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
        if "question" not in extracted_data or not extracted_data["question"]:
            extracted_data["question"] = "你有什么特点？在合适的场景下，你的特点会变成优点吗？"
        col1, col2 = st.columns([1, 1])
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
                scene = extracted_data.get("scene", "")
                edited_scene = st.text_input("📍 场景", value=scene)
                extracted_data["scene"] = edited_scene
            else:
                viewpoints_str = ", ".join(extracted_data.get("viewpoints", ["观点1", "观点2"]))
                edited_viewpoints = st.text_input("💬 可能的观点", value=viewpoints_str)
                extracted_data["viewpoints"] = [v.strip() for v in edited_viewpoints.split(",") if v.strip()]
                if not extracted_data["viewpoints"]:
                    extracted_data["viewpoints"] = ["赞成", "反对"]
        with col2:
            question = extracted_data.get("question", "")
            edited_question = st.text_area("💬 核心问题（模拟发言将围绕这个问题展开）", value=question, height=120)
            extracted_data["question"] = edited_question
            if script_type == "事件型":
                items_str = ", ".join(extracted_data.get("items", ["作品", "东西"]))
                edited_items = st.text_input("📦 关键物品", value=items_str)
                extracted_data["items"] = [i.strip() for i in edited_items.split(",") if i.strip()]
                if not extracted_data["items"]:
                    extracted_data["items"] = ["作品", "东西"]
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
        extracted_data = st.session_state["extracted_data"]
        script_type = st.session_state.get("script_type", "事件型")
        question = extracted_data.get("question", "你有什么特点？在合适的场景下，你的特点会变成优点吗？")
        st.info("💬 核心问题：**" + question + "**")
        speeches = []
        for _ in range(samples_per_type):
            for speech_type in test_types:
                speech_text = get_speech_for_grade(grade, speech_type, extracted_data, script_type)
                speech_desc = next((t["desc"] for t in SPEECH_TYPES_CONFIG if t["id"] == speech_type), speech_type)
                speeches.append({"type": speech_type, "desc": speech_desc, "speech": speech_text})
        st.success("✅ 已生成 " + str(len(speeches)) + " 条模拟发言（围绕核心问题生成）")
        ai_configs = parse_ai_configs(ai_configs_input)
        if not ai_configs:
            st.error("AI指令词解析失败")
            st.stop()
        st.success("✅ 已解析 " + str(len(ai_configs)) + " 个AI")
        for c in ai_configs:
            st.caption("  - " + c['name'] + " (" + c['role'] + ")")
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
                results.append({"AI名称": ai_config["name"], "AI角色": ai_config["role"], "原始指令词": ai_config["prompt"], "发言类型": speech["type"], "发言说明": speech["desc"], "模拟发言": speech["speech"], "AI点评": feedback})
                time.sleep(0.2)
        status_text.text("✅ 测试完成！")
        progress_bar.progress(1.0)
        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.success("🎉 测试完成！共 " + str(len(results)) + " 条点评记录")
        st.subheader("📋 诊断与优化结果")
        all_diagnoses = []
        for ai_name in df["AI名称"].unique():
            ai_df = df[df["AI名称"] == ai_name]
            ai_role = ai_df["AI角色"].iloc[0]
            ai_prompt = ai_df["原始指令词"].iloc[0]
            with st.spinner("🔍 正在分析 " + ai_name + " 并生成优化方案..."):
                diagnosis = diagnose_ai_performance(ai_name, ai_role, ai_prompt, ai_df, api_key, base_url, model)
                all_diagnoses.append({"name": ai_name, "role": ai_role, "original_prompt": ai_prompt, "issues": diagnosis["issues"], "strengths": diagnosis["strengths"], "warnings": diagnosis["warnings"], "total_issues": diagnosis["total_issues"], "total_strengths": diagnosis["total_strengths"], "total_warnings": diagnosis["total_warnings"], "optimized_prompt": diagnosis["optimized_prompt"]})
                time.sleep(0.3)
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
                if diag["optimized_prompt"] and "优化失败" not in diag["optimized_prompt"]:
                    st.markdown("---")
                    st.markdown("**✨ AI自动优化后的指令词**")
                    st.caption("🟢 绿色行 = 新增或修改的内容")
                    highlighted, changes = highlight_diff(diag["original_prompt"], diag["optimized_prompt"])
                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.markdown("**📄 原始版本**")
                        st.code(diag["original_prompt"], language="text")
                    with col_right:
                        st.markdown("**📝 优化版本（🟢标注变更）**")
                        st.code(highlighted, language="text")
                    st.download_button(label="📋 下载 " + diag['name'] + " 优化版", data=diag["optimized_prompt"], file_name=diag['name'] + "_优化版.txt", mime="text/plain", key="download_" + diag['name'] + "_" + timestamp)
                    st.caption("💡 直接复制右侧优化版本，替换你原来的指令词即可")
                else:
                    st.markdown("---")
                    st.markdown("🎉 **该AI表现良好，无需优化！**")
                st.markdown("---")
                st.markdown("**📝 详细测试记录**")
                ai_df = df[df["AI名称"] == diag["name"]]
                for _, row in ai_df.iterrows():
                    with st.expander("📌 " + row['发言说明']):
                        st.markdown("**核心问题：**")
                        st.info(question)
                        st.markdown("**模拟发言：**")
                        st.info(row["模拟发言"])
                        st.markdown("**AI回复：**")
                        st.text(row["AI点评"])
        st.subheader("📊 总体概览")
        summary_data = []
        for diag in all_diagnoses:
            has_optimized = diag["optimized_prompt"] and "优化失败" not in diag["optimized_prompt"]
            summary_data.append({"AI名称": diag["name"], "角色": diag["role"], "问题数": diag["total_issues"], "优点数": diag["total_strengths"], "状态": "⚠️ 已优化" if diag["total_issues"] > 0 else "✅ 良好", "有优化版": "是" if has_optimized else "否"})
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        optimized_texts = []
        for diag in all_diagnoses:
            if diag["optimized_prompt"] and "优化失败" not in diag["optimized_prompt"]:
                optimized_texts.append("【" + diag['name'] + "】\n" + diag['optimized_prompt'] + "\n")
        if optimized_texts:
            all_optimized = "\n=== 分隔 ===\n".join(optimized_texts)
            st.download_button(label="📥 一键下载所有优化版指令词", data=all_optimized, file_name="所有优化版指令词_" + course_name + "_" + timestamp + ".txt", mime="text/plain")
        save_data = {"course": course_name, "timestamp": timestamp, "ai_count": len(ai_configs), "ai_names": [c["name"] for c in ai_configs], "question": question, "diagnoses": all_diagnoses}
        with open(os.path.join(HISTORY_DIR, course_name + "_" + timestamp + ".json"), "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        st.caption("💾 已保存至历史记录")
