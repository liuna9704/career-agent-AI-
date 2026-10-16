RESUME_ANALYSIS_PROMPT = """你是一名专业HR和技术面试官。请分析以下简历文本，并只输出一个严格合法的JSON对象，不要输出Markdown代码块、解释或额外文字。

输出结构：
{{
  "name": "",
  "education": "",
  "major": "",
  "target_job": "",
  "skills": [],
  "projects": [
    {{
      "name": "",
      "technology": "",
      "responsibility": "",
      "result": ""
    }}
  ],
  "advantages": [],
  "weaknesses": [],
  "potential_questions": []
}}

分析要求：
1. 不允许编造简历中不存在的信息。
2. 无法判断的字符串字段填写“未知”，无法判断的列表填写空数组。
3. 项目必须提取候选人的个人职责；未说明职责时填写“未知”。
4. 将描述模糊、缺少数据或需要核验的信息写入potential_questions。
5. skills仅保留简历中明确出现的技能。
6. 优势和不足必须能从简历文本中找到依据。

简历文本：
---
{resume_text}
---
"""


def build_resume_prompt(resume_text: str) -> str:
    return RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text[:30000])

