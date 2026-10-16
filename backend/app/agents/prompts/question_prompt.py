import json


def build_question_prompt(state: dict, context: list[dict]) -> str:
    return f"""你是一名高级技术面试官，请生成一个且仅一个针对性面试问题。
候选人画像：{json.dumps(state.get('candidate_profile', {}), ensure_ascii=False)}
岗位：{state.get('job')}
当前阶段：{state.get('current_stage')}
当前能力：{state.get('current_ability')}
当前能力评价模型：{json.dumps(next((item for item in state.get('competency_model', []) if item.get('name') == state.get('current_ability')), {}), ensure_ascii=False)}
当前项目上下文：{json.dumps(state.get('current_project_context', {}), ensure_ascii=False)}
决策动作：{state.get('next_action', 'initial')}
最近回答：{json.dumps(state.get('messages', [])[-2:], ensure_ascii=False)}
岗位RAG上下文：{json.dumps(context, ensure_ascii=False)}
已覆盖能力：{json.dumps(state.get('covered_abilities', []), ensure_ascii=False)}
要求：优先从当前能力模型的面试验证点中选择考察方向，并结合简历或最近回答；不得照抄固定题；一次只问一个核心问题；深入追问时引用回答中的技术点；澄清时指出缺失信息。若当前项目上下文已有project_name，问题必须继续围绕该项目，不得引用候选人的其他项目；只有项目证据充分且决策明确切换后才允许更换项目。问题所考察内容必须与当前能力一致。
只输出严格JSON：{{"question":"问题文本"}}"""
