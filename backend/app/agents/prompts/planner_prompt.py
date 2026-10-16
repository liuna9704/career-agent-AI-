import json


def build_planner_prompt(candidate: dict, job: str, competencies: list[dict]) -> str:
    return f"""你是一名高级面试官，请为候选人规划一场岗位面试。
候选人画像：{json.dumps(candidate, ensure_ascii=False)}
目标岗位：{job}
选手自建岗位胜任力模型：{json.dumps(competencies, ensure_ascii=False)}
请优先验证简历中明确出现的技能和待核验信息，并覆盖胜任力模型的核心维度。plan中的ability必须优先使用模型中的能力名称。
只输出严格JSON：{{"plan":[{{"stage":"基础能力|项目深入追问|业务场景|压力测试","ability":"能力名称","reason":"考察原因"}}]}}
plan包含4到6项，不要输出其他内容。"""
