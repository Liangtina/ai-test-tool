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

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="AI指令词诊断与自动优化工具",
    page_icon="🔬",
    layout="wide"
)

# ============================================================
# 数据存储
# ============================================================

HISTORY_DIR = "test_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# ============================================================
# 模拟学生发言生成器
# ============================================================

STUDENT_SPEECH_TEMPLATES = {
    "完整优秀": {
        "desc": "✅ 完整发言（物品改造+多个特点+明确理由）",
        "template": "大家好，我叫{name}。{item_intro}，我把它们{action}，变成了{new_use}。我觉得自己有{count}个特点。一个是{trait1}，一个是{trait2}。我觉得{trait1}适合当{job1}，因为{reason1}。我还觉得{trait2}适合当{job2}，因为{reason2}。"
    },
    "完整优秀_单特点多工作": {
        "desc": "✅ 一个特点对应多个工作",
        "template": "大家好，我叫{name}。{item_intro}，我把它们{action}，变成了{new_use}。我有一个特点，就是{trait1}。我觉得这个特点适合当{job1}，因为{reason1}。还适合当{job2}，因为{reason2}。"
    },
    "缺为什么": {
        "desc": "⚠️ 说了特点和对应工作，但没说为什么适合",
        "template": "大家好，我叫{name}。{item_intro}，我把它们{action}，变成了{new_use}。我觉得自己{trait1}，适合当{job1}。"
    },
    "只说了物品没说特点": {
        "desc": "⚠️ 只说了物品改造，完全没提自己特点和工作",
        "template": "大家好，我叫{name}。我家有{item_intro}，我把它们{action}，变成了{new_use}。"
    },
    "只说了特点没说工作": {
        "desc": "⚠️ 只说了自己特点，没说对应什么工作",
        "template": "大家好，我叫{name}。我觉得自己{trait1}，还{trait2}。"
    },
    "只说了特点缺工作缺理由": {
        "desc": "⚠️ 只说了特点，工作和理由都没有",
        "template": "大家好，我叫{name}。我很{trait1}，也很{trait2}。"
    },
    "过于简短": {
        "desc": "⚠️ 一句话带过，信息极度缺失",
        "template": "我叫{name}。我喜欢{trait1}。"
    },
    "特点模糊不具体": {
        "desc": "⚠️ 特点很模糊（好/厉害等），工作也没有理由",
        "template": "大家好，我叫{name}。{item_intro}，我把它们{action}，变成了{new_use}。我觉得自己比较{fuzzy_trait}，可能适合当{job1}吧。"
    },
    "逻辑牵强": {
        "desc": "⚠️ 特点和工作的匹配逻辑不通顺",
        "template": "大家好，我叫{name}。{item_intro}，我把它们{action}，变成了{new_use}。我喜欢{trait1}，所以我觉得适合当{job1}。"
    }
}

NAMES = ["小星", "小明", "小丽", "小刚", "小美", "小乐", "小花", "小胖", "小雪", "小宇"]
ITEMS = [("旧报纸", "折", "小纸盒"), ("旧鞋盒", "剪开", "小房子屋顶"), ("空玻璃瓶", "洗干净插花", "花瓶"), ("旧T恤", "剪成布条编", "小篮子"), ("彩色扣子", "穿成", "项链"), ("奶粉罐", "包上彩纸", "笔筒"), ("旧纸箱", "裁开粘", "小书架"), ("用完的笔芯", "捆在一起", "小栅栏")]
TRAITS = [
    ("跑得快", "快递员", "快递员要快快地送包裹"),
    ("嗓门大", "体育老师", "体育老师在操场喊口令需要大声"),
    ("安静", "图书管理员", "图书管理员要安安静静地整理书"),
    ("爱观察", "科学家", "科学家要仔细观察才能发现秘密"),
    ("爱笑", "幼儿园老师", "小朋友看到老师笑就会很开心"),
    ("会安慰人", "医生", "病人难受时需要有人温柔地安慰"),
    ("力气大", "消防员", "消防员要搬很重的东西救人"),
    ("画画好", "设计师", "设计师要画很多图纸"),
    ("喜欢说话", "主持人", "主持人要一直说话不紧张"),
    ("有耐心", "老师", "老师要一遍一遍教小朋友"),
    ("喜欢小动物", "兽医", "兽医要照顾小动物"),
    ("手巧", "手工老师", "手工老师要教小朋友做东西"),
]
FUZZY_TRAITS = ["好", "厉害", "不错", "还行", "还可以"]
JOBS = ["厨师", "司机", "警察", "护士", "建筑师", "飞行员", "画家", "歌手", "舞蹈老师"]


def generate_student_speech(speech_type):
    name = random.choice(NAMES)
    item, action, new_use = random.choice(ITEMS)
    trait1, job1, reason1 = random.choice(TRAITS)
    remaining = [t for t in TRAITS if t[0] != trait1]
    trait2, job2, reason2 = random.choice(remaining) if remaining else random.choice(TRAITS)
    config = STUDENT_SPEECH_TEMPLATES.get(speech_type, STUDENT_SPEECH_TEMPLATES["完整优秀"])
    template = config["template"]
    
    if speech_type == "完整优秀":
        return template.format(name=name, item_intro=f"我家有好多{item}", action=action, new_use=new_use, count=2, trait1=trait1, trait2=trait2, job1=job1, job2=job2, reason1=reason1, reason2=reason2)
    elif speech_type == "完整优秀_单特点多工作":
        return template.format(name=name, item_intro=f"我家有好多{item}", action=action, new_use=new_use, trait1=trait1, job1=job1, job2=job2, reason1=reason1, reason2=reason2)
    elif speech_type == "缺为什么":
        return template.format(name=name, item_intro=f"我家有好多{item}", action=action, new_use=new_use, trait1=trait1, job1=job1)
    elif speech_type == "只说了物品没说特点":
        return template.format(name=name, item_intro=f"好多{item}", action=action, new_use=new_use)
    elif speech_type in ["只说了特点没说工作", "只说了特点缺工作缺理由"]:
        return template.format(name=name, trait1=trait1, trait2=trait2)
    elif speech_type == "过于简短":
        return template.format(name=name, trait1=trait1)
    elif speech_type == "特点模糊不具体":
        fuzzy = random.choice(FUZZY_TRAITS)
        job = random.choice(JOBS)
        return template.format(name=name, item_intro=f"好多{item}", action=action, new_use=new_use, fuzzy_trait=fuzzy, job1=job)
    elif speech_type == "逻辑牵强":
        wrong_job = random.choice([j for j in JOBS if j != job1]) if len(JOBS) > 1 else "厨师"
        return template.format(name=name, item_intro=f"好多{item}", action=action, new_use=new_use, trait1=trait1, job1=wrong_job)
    return ""


def generate_all_test_speeches(test_types, samples_per_type):
    speeches = []
    for _ in range(samples_per_type):
        for speech_type in test_types:
            speech = generate_student_speech(speech_type)
            speeches.append({"type": speech_type, "desc": STUDENT_SPEECH_TEMPLATES[speech_type]["desc"], "speech": speech})
    return speeches


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
        return f"【调用失败】{str(e)}"


# ============================================================
# 对比指令词差异（标注修改位置）
# ============================================================

def highlight_diff(original, optimized):
    """对比两个指令词，标注新增/修改的部分"""
    if not optimized or not original:
        return optimized, []
    
    orig_lines = original.split('\n')
    opt_lines = optimized.split('\n')
    
    diff = list(difflib.unified_diff(
        orig_lines, opt_lines,
        fromfile='原始', tofile='优化后',
        lineterm=''
    ))
    
    # 提取变更的位置
    changes = []
    import re
    for line in diff:
        if line.startswith('@@'):
            match = re.search(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
            if match:
                old_start = int(match.group(1))
                new_start = int(match.group(2))
                changes.append({'old_start': old_start, 'new_start': new_start})
    
    # 生成带标注的版本
    highlighted = []
    for i, line in enumerate(opt_lines):
        is_changed = False
        for change in changes:
            if change['new_start'] <= i + 1 <= change['new_start'] + 3:
                is_changed = True
                break
        if is_changed:
            highlighted.append(f"🟢 {line}")
        else:
            highlighted.append(f"   {line}")
    
    return '\n'.join(highlighted), changes


# ============================================================
# 核心：诊断 + 自动优化
# ============================================================

def diagnose_ai_performance(ai_name, ai_role, ai_prompt, df_results, api_key, base_url, model):
    """诊断AI表现并生成优化后的指令词"""
    
    issues = []
    strengths = []
    warnings = []
    
    for _, row in df_results.iterrows():
        speech_type = row["发言类型"]
        desc = row["发言说明"]
        feedback = row["AI点评"]
        
        if "点评" in ai_name or "评价" in ai_name:
            if not any(k in feedback for k in ["评级", "推荐", "维度", "综合"]):
                issues.append(f"未按格式输出（缺评级/维度/综合结构）— 发言类型: {desc}")
            elif "评级" not in feedback and "推荐" not in feedback[:200]:
                warnings.append(f"格式不完整，可能缺少评级 — {desc}")
        
        incomplete_types = ["缺为什么", "只说了物品没说特点", "只说了特点没说工作", "只说了特点缺工作缺理由", "过于简短", "特点模糊不具体"]
        if speech_type in incomplete_types:
            has_question = any(k in feedback for k in ["为什么", "补充", "具体", "理由", "说说", "哪些", "怎样"])
            if not has_question:
                issues.append(f"对不完整发言未追问缺失信息 — {desc}")
            else:
                strengths.append(f"能主动追问缺失信息 — {desc}")
        
        if speech_type == "只说了物品没说特点" and "特点" not in feedback and "工作" not in feedback:
            issues.append(f"点评与发言内容不匹配，可能跑题 — {desc}")
        
        if speech_type in ["完整优秀", "完整优秀_单特点多工作"]:
            if any(k in feedback for k in ["棒", "好", "优秀", "完整", "清楚"]):
                strengths.append(f"对完整发言肯定到位 — {desc}")
            else:
                warnings.append(f"对完整发言未给予足够肯定 — {desc}")
        
        if "回应" in ai_name:
            if not any(k in feedback for k in ["你说得", "我同意", "是的", "对呀", "没错"]):
                warnings.append(f"回应类AI缺乏互动感 — {desc}")
        
        if "总结" in ai_name:
            if not any(k in feedback for k in ["总结", "归纳", "整理", "综合"]):
                issues.append(f"总结类AI未做归纳总结 — {desc}")
        
        word_count = len(feedback)
        if word_count < 20:
            warnings.append(f"点评过短（{word_count}字），不够充分 — {desc}")
        elif word_count > 1000:
            warnings.append(f"点评过长（{word_count}字），需要精简 — {desc}")
    
    issues = list(dict.fromkeys(issues))
    strengths = list(dict.fromkeys(strengths))
    warnings = list(dict.fromkeys(warnings))
    
    optimized_prompt = None
    
    if issues or warnings:
        optimization_request = f"""
【任务】优化以下AI指令词，解决诊断中发现的问题。

【原始指令词】
{ai_prompt}

【AI角色】
{ai_role}

【诊断出的问题】
{chr(10).join(['- ' + i for i in issues]) if issues else '无严重问题'}

【需要注意的点】
{chr(10).join(['- ' + w for w in warnings]) if warnings else '无'}

【优化要求】
1. 针对以上每个问题，在指令词中增加或修改对应的要求
2. 保持原有风格和语气不变
3. 只输出优化后的完整指令词，不要输出任何解释或说明
4. 确保优化后的指令词是可直接复制使用的完整版本
5. 如果问题中提到"未按格式输出"，请在指令词中明确写出输出格式模板
6. 如果问题中提到"未追问"，请在指令词中增加明确的追问要求

请输出优化后的完整指令词：
"""
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一位AI指令词优化专家。你擅长根据测试反馈精准修改指令词，解决具体问题。"},
                    {"role": "user", "content": optimization_request}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            optimized_prompt = response.choices[0].message.content
        except Exception as e:
            optimized_prompt = f"【优化失败】{str(e)}"
    
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

st.title("🔬 AI指令词诊断与自动优化工具")
st.markdown("测试所有AI → 自动诊断问题 → AI自动生成优化后的指令词")

with st.sidebar:
    st.header("📋 功能")
    menu = st.radio("选择操作", ["🆕 新建测试", "📚 历史记录", "📖 说明"])
    
    st.divider()
    
    st.subheader("🔑 API配置")
    api_key = st.text_input("API Key", type="password", placeholder="输入你的API Key", key="api_key_input")
    base_url = st.text_input("Base URL", value="https://api.deepseek.com", key="base_url_input")
    model = st.text_input("模型", value="deepseek-chat", key="model_input")
    
    st.caption(f"📁 历史记录: {len(os.listdir(HISTORY_DIR))} 条")

if menu == "📖 说明":
    st.markdown("""
    ## 📖 使用说明
    
    每节课你需要"捏制"多个AI，每个AI承担不同角色（点评、总结、回应等）。
    
    这个工具会：
    1. **测试**：用模拟学生发言测试每个AI
    2. **诊断**：自动找出每个AI指令词中的问题
    3. **优化**：AI自动生成优化后的新指令词，并标注修改位置
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
            st.caption(f"📅 {r['course']} - {r['time']} ({r['ai_count']}个AI)")

else:
    col1, col2 = st.columns([1, 2])
    with col1:
        course_name = st.text_input("📚 课程名称", placeholder="如：第1课_礼物改造")
    with col2:
        st.caption("💡 用于保存历史记录")
    
    st.subheader("🤖 输入本节课所有AI指令词")
    st.caption("每个AI用 === 分隔，第一行为AI名称（如【点评AI_温柔版】）")
    
    ai_configs_input = st.text_area(
        "AI指令词",
        height=350,
        placeholder="""【点评AI_温柔版】
你是一位温柔的一二年级老师，负责点评学生发言。请按照以下格式输出：
【推荐评级】xxx
【维度详评】xxx
【综合点评】xxx
===
【点评AI_严格版】
你是一位严格的一二年级老师...
===
【回应AI】
你是一位亲切的老师，负责回应学生发言..."""
    )
    
    st.subheader("📝 测试设置")
    col1, col2 = st.columns([2, 1])
    with col1:
        test_types = st.multiselect(
            "选择测试类型",
            options=list(STUDENT_SPEECH_TEMPLATES.keys()),
            format_func=lambda x: STUDENT_SPEECH_TEMPLATES[x]["desc"],
            default=list(STUDENT_SPEECH_TEMPLATES.keys())
        )
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
        
        ai_configs = parse_ai_configs(ai_configs_input)
        if not ai_configs:
            st.error("AI指令词解析失败")
            st.stop()
        
        st.success(f"✅ 已解析 {len(ai_configs)} 个AI")
        for c in ai_configs:
            st.caption(f"  - {c['name']} ({c['role']})")
        
        speeches = generate_all_test_speeches(test_types, samples_per_type)
        st.success(f"✅ 已生成 {len(speeches)} 条模拟发言")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total = len(ai_configs) * len(speeches)
        idx = 0
        
        for ai_config in ai_configs:
            for speech in speeches:
                idx += 1
                status_text.text(f"⏳ 测试中: {ai_config['name']} × {speech['type']} ({idx}/{total})")
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
        
        st.success(f"🎉 测试完成！共 {len(results)} 条点评记录")
        
        st.subheader("📋 诊断与优化结果")
        
        all_diagnoses = []
        
        for ai_name in df["AI名称"].unique():
            ai_df = df[df["AI名称"] == ai_name]
            ai_role = ai_df["AI角色"].iloc[0]
            ai_prompt = ai_df["原始指令词"].iloc[0]
            
            with st.spinner(f"🔍 正在分析 {ai_name} 并生成优化方案..."):
                diagnosis = diagnose_ai_performance(ai_name, ai_role, ai_prompt, ai_df, api_key, base_url, model)
                all_diagnoses.append({
                    "name": ai_name,
                    "role": ai_role,
                    "original_prompt": ai_prompt,
                    **diagnosis
                })
                time.sleep(0.3)
        
        # ---- 显示诊断结果（带差异标注和下拉菜单） ----
        for diag in all_diagnoses:
            status_icon = "✅" if not diag["issues"] else "⚠️"
            with st.expander(f"{status_icon} {diag['name']} ({diag['role']}) — 问题: {diag['total_issues']}个", expanded=True):
                
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
                        st.markdown(f"- {s}")
                
                if diag["issues"]:
                    st.markdown("**❌ 需要修改的问题：**")
                    for issue in diag["issues"]:
                        st.markdown(f"- {issue}")
                
                if diag["warnings"]:
                    st.markdown("**🟡 值得注意：**")
                    for w in diag["warnings"]:
                        st.markdown(f"- {w}")
                
                # ---- 优化后的指令词（带差异标注） ----
                if diag["optimized_prompt"] and "【优化失败】" not in diag["optimized_prompt"]:
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
                    
                    st.download_button(
                        label=f"📋 下载 {diag['name']} 优化版",
                        data=diag["optimized_prompt"],
                        file_name=f"{diag['name']}_优化版.txt",
                        mime="text/plain",
                        key=f"download_{diag['name']}_{timestamp}"
                    )
                    st.caption("💡 直接复制右侧优化版本，替换你原来的指令词即可")
                else:
                    st.markdown("---")
                    st.markdown("🎉 **该AI表现良好，无需优化！**")
                
                # ---- 详细测试记录（下拉菜单查看模拟发言） ----
                st.markdown("---")
                st.markdown("**📝 详细测试记录**")
                ai_df = df[df["AI名称"] == diag["name"]]
                for _, row in ai_df.iterrows():
                    with st.expander(f"📌 {row['发言说明']}"):
                        st.markdown("**模拟发言：**")
                        st.info(row["模拟发言"])
                        st.markdown("**AI回复：**")
                        st.text(row["AI点评"])
        
        # ---- 总体概览 ----
        st.subheader("📊 总体概览")
        
        summary_data = []
        for diag in all_diagnoses:
            summary_data.append({
                "AI名称": diag["name"],
                "角色": diag["role"],
                "问题数": diag["total_issues"],
                "优点数": diag["total_strengths"],
                "状态": "⚠️ 已优化" if diag["total_issues"] > 0 else "✅ 良好",
                "有优化版": "是" if diag["optimized_prompt"] and "【优化失败】" not in diag["optimized_prompt"] else "否"
            })
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        
        optimized_texts = []
        for diag in all_diagnoses:
            if diag["optimized_prompt"] and "【优化失败】" not in diag["optimized_prompt"]:
                optimized_texts.append(f"【{diag['name']}】\n{diag['optimized_prompt']}\n")
        
        if optimized_texts:
            all_optimized = "\n=== 分隔 ===\n".join(optimized_texts)
            st.download_button(
                label="📥 一键下载所有优化版指令词",
                data=all_optimized,
                file_name=f"所有优化版指令词_{course_name}_{timestamp}.txt",
                mime="text/plain"
            )
        
        save_data = {
            "course": course_name,
            "timestamp": timestamp,
            "ai_count": len(ai_configs),
            "ai_names": [c["name"] for c in ai_configs],
            "diagnoses": all_diagnoses
        }
        with open(os.path.join(HISTORY_DIR, f"{course_name}_{timestamp}.json"), "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        st.caption(f"💾 已保存至历史记录")
        
      
