import json


def build_analyze_prompt(state: dict, answer: str) -> str:
    return f"""你是一名专业技术面试评估员，请分析候选人的最新回答。
目标岗位：{state.get('job')}
当前能力：{state.get('current_ability')}
当前能力评价指标与评分标准：{json.dumps(next((item for item in state.get('competency_model', []) if item.get('name') == state.get('current_ability')), {}), ensure_ascii=False)}
当前问题：{state.get('current_question')}
当前项目上下文：{json.dumps(state.get('current_project_context', {}), ensure_ascii=False)}
候选人回答：{answer}
历史证据：{json.dumps(state.get('evidences', []), ensure_ascii=False)}
必须依据当前胜任力模型的评价指标和评分标准，分别判断相关性、完整性、技术深度、量化程度、真实性和逻辑性。不允许推断回答中没有的信息。
识别回答正在讨论的具体项目、实际体现的能力维度和技术点。能力必须与回答一致，例如Vue3页面为“前端工程能力”，FastAPI接口为“后端接口开发能力”，大模型调用为“AI应用开发能力”。已有当前项目时，除非回答明确表示已结束并切换项目，否则不得将其他简历项目混入分析。
只输出严格JSON：{{"quality":"good|normal|needs_clarification","ability":"识别出的能力","project_detected":"回答中的项目名或空字符串","ability_detected":"动态能力维度","technical_points":["技术点"],"evidence":"一条忠实于回答的能力证据","confidence":0,"relevance":0,"completeness":0,"depth":0,"quantification":0,"authenticity":0,"logic":0,"missing":["缺失点"],"keywords":["技术关键词"]}}
六项评分均为0到100整数。"""
