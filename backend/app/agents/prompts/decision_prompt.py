import json


def build_decision_prompt(state: dict) -> str:
    return f"""你是面试流程决策器，请根据回答分析选择下一动作。
当前能力：{state.get('current_ability')}
回答分析：{json.dumps(state.get('answer_analysis', {}), ensure_ascii=False)}
当前能力已提问次数：{state.get('ability_question_counts', {}).get(state.get('current_ability'), 0)}
已覆盖：{json.dumps(state.get('covered_abilities', []), ensure_ascii=False)}
待覆盖：{json.dumps(state.get('pending_abilities', []), ensure_ascii=False)}
总问题数：{state.get('question_count', 0)}/10
规则：信息不足选clarify；出现值得验证的技术细节选deep_question；当前能力证据充分选switch_ability；全部完成或达到10题选finish。单项能力最多连续追问2次。
只输出严格JSON：{{"action":"deep_question|clarify|switch_ability|finish","reason":"决策原因"}}"""

