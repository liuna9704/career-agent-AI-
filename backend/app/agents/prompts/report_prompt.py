import json


def build_report_prompt(state: dict) -> str:
    return f"""你是一名专业HR，请根据能力证据生成面试结束摘要。
岗位：{state.get('job')}
能力证据：{json.dumps(state.get('evidences', []), ensure_ascii=False)}
回答分析：{json.dumps(state.get('answer_analysis', {}), ensure_ascii=False)}
只输出严格JSON：{{"evidence_count":0,"covered_abilities":[],"scoring_basis":["评分依据"],"summary":"总结"}}。不得编造。"""

