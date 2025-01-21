#%%
import fitz  # PyMuPDF


# 시험별로 바꿈
test_id = "Odd_Kor_3rd_2024_11"


# PDF에서 텍스트 추출
def extract_text_with_pymupdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        extracted_text = ""
        for page in doc:
            extracted_text += page.get_text()
        return extracted_text
    except Exception as e:
        return f"Error: {e}"


# 파일 경로
pdf_path = 'LLM/평가원기출문제_국어_홀수/Kor_3rd_2022_03.pdf'

# 저장 파일 경로
json_path = 'LLM/Kor/'

# 텍스트 추출
text = extract_text_with_pymupdf(pdf_path)

# # 텍스트 확인
# print(text)

# %%
# 제거할 텍스트 패턴 정의
import re
unwanted_patterns = [
    r"이 문제지에 관한 저작권은 한국교육과정평가원에 있습니다.*?홀수형\s*\d+\s*\d+\s*\d+",
    r"\d{4}학년도\s*\d{1,2}월\s*고\d{1,2}\s*전국연합학력평가\s*문제지\s*국어영역\s*제1 교시",
    r"\d{4}학년도\s*대학수학능력시험\s*\d{1,2}월\s*모의평가\s*문제지\s*국어영역\s*제1 교시",
    r"고\d{1,2}\s*국어영역.*?\d+",  # 공백 포함 버전
    r"\d+\[A\]\d+국어영역고\d+\d+",
    r"\d+국어영역고\d+",  # 예: "8국어영역고3820"
    r"고\d{1,2}국어영역\d+",  # 예: "고3국어영역111120"
    r"고\d{1,2}국어영역\(.*?\)\d+"  # 예: "고3국어영역(화법과작문)31520",
    r"이 문제지에 관한 저작권은 한국교육과정평가원에 있습니다.",
    r"\d{4}학년도 대학수학능력시험 \d{1}월 모의평가 문제지.*?\s*\[A\]\s*제1 교시\s*홀수형",
    r"\* 확인 사항.*?하시오",
    r"\d{4}학년도 대학수학능력시험 \d{1}월 모의평가 문제지.*?\s*제1 교시\s*홀수형",
    r"\d{4}학년도 대학수학능력시험.*?제1 교시",
    r"이어서,.*?확인하시오\.",
    r"\[3점\]",
    r"\(화법과 작문\)\s*\d+\s*\d+\s*\d+",  # "(화법과 작문) 3 15 20" 패턴 제거
    r"홀수형\s*\d+\s*\d+\s*\d+"  # "홀수형 3 15 20" 패턴 제거
]

# 섹션 분리 (예: [1～3], [4～9])
sections = re.split(r"(\[\d+\s*~\s*\d+\])", text)

parsed_sections = []
current_section = None

for part in sections:
    part = part.strip()
    if re.match(r"\[\d+\s*~\s*\d+\]", part):  # 섹션 번호
        if current_section:  # 이전 섹션 저장
            # 첫 번째 질문을 paragraph로 옮기기
            if current_section["problems"]:
                first_question = current_section["problems"].pop(0)
                current_section["paragraph"] += "\n" + first_question
            parsed_sections.append(current_section)
        current_section = {"section": part, "paragraph": "", "problems": []}
    elif current_section:  # 본문 또는 문제 추가
        # 문제 감지 (숫자. 으로 시작하는 경우)
        question_match = re.search(r"^\d{1,2}\.", part, re.MULTILINE)
        if question_match:
            # 문제 부분 분리 후 questions에 추가
            problems = re.split(r"^\d{1,2}\.", part, flags=re.MULTILINE)
            cleaned_questions = []
            for q in problems:
                # 불필요한 텍스트 제거
                for pattern in unwanted_patterns:
                    q = re.sub(pattern, "", q, flags=re.DOTALL).strip()
                if q:
                    cleaned_questions.append(q)
            current_section["problems"].extend(cleaned_questions)

# 마지막 지문 처리
if current_section:
    # 첫 번째 질문을 paragraph로 옮기기
    if current_section["problems"]:
        first_question = current_section["problems"].pop(0)
        current_section["paragraph"] += "\n" + first_question
    parsed_sections.append(current_section)


# 섹션 처리 및 출력
for i, section in enumerate(parsed_sections, 1):
    # 첫 줄바꿈 전까지 제거
    if "paragraph" in section and section["paragraph"].strip():
        section["paragraph"] = "\n".join(section["paragraph"].split("\n")[2:]).strip()

# 줄바꿈 제거 적용
for section in parsed_sections:
    if section["paragraph"]:
        section["paragraph"] = section["paragraph"].replace("\n", "").strip()

    for i, problem in enumerate(section["problems"]):
        section["problems"][i] = problem.replace("\n", "").strip()

# 문제를 세부적으로 분리하여 question, question_plus, choices로 나누는 작업
for section in parsed_sections:
    new_problems = []  # 새로운 구조의 문제 리스트
    for problem in section["problems"]:
        question = ""
        question_plus = ""
        choices = []

        # <보 기> 이후 부분을 찾고 나눔
        if "< 보 기 >" in problem:
            parts = problem.split("< 보 기 >", 1)
            question = parts[0].strip()
            remaining = parts[1].strip()

            # 선택지를 구분 (①, ② 등의 패턴으로 시작하는 부분)
            choices_split = re.split(r"(?=①|②|③|④|⑤)", remaining, maxsplit=1)
            if len(choices_split) == 2:
                question_plus = choices_split[0].strip()
                choices = re.split(r"①|②|③|④|⑤", choices_split[1])
                choices = [c.strip() for c in choices if c.strip()]
            else:
                question_plus = remaining
        else:
            # 선택지를 구분 (①, ② 등의 패턴으로 시작하는 부분)
            choices_split = re.split(r"(?=①|②|③|④|⑤)", problem, maxsplit=1)
            if len(choices_split) == 2:
                question = choices_split[0].strip()
                choices = re.split(r"①|②|③|④|⑤", choices_split[1])
                choices = [c.strip() for c in choices if c.strip()]
            else:
                question = problem.strip()

        # 새로운 문제 구조 추가
        new_problems.append({
            "question": question,
            "question_plus": question_plus,
            "choices": choices
        })

    # 기존 problems를 새로운 구조로 대체
    section["problems"] = new_problems

# # 중간 결과 확인
# for i, section in enumerate(parsed_sections, 1):
#     print(f"Section {i}: {section['section']}")
#     print(f"Paragraph: {section['paragraph']}")
#     print("Problems:")
#     for problem in section["problems"]:
#         print(f"- Question: {problem['question']}")
#         if problem["question_plus"]:
#             print(f"  Question Plus: {problem['question_plus']}")
#         if problem["choices"]:
#             print(f"  Choices: {', '.join(problem['choices'])}")
#     print("\n---\n")



#%%
# json으로 변환
import json
import re

def format_section_id(section):
    # 섹션 번호에서 [1 ~ 3]을 Odd_Kor_3rd_2025_01-03으로 변환
    match = re.match(r"\[(\d+)\s*~\s*(\d+)\]", section)
    if match:
        start, end = match.groups()
        return f"{test_id}_{start.zfill(2)}-{end.zfill(2)}"
    return "Unknown_ID"


# 문제 번호를 위한 전역 카운터
problem_counter = 1

# 결과 데이터 초기화
result_data = []

# 섹션을 순회하면서 JSON 구조로 변환
for section_index, section in enumerate(parsed_sections, 1):
    section_id = format_section_id(section['section'])
    paragraph = section["paragraph"]
    problems = []

    for problem_index, problem in enumerate(section["problems"], 1):
        # 문제 데이터 초기화
        question = problem.get("question", "").strip()
        question_plus = problem.get("question_plus", "").strip()
        choices = problem.get("choices", [])

        # 문제 ID 생성
        question_id = f"{test_id}_{problem_counter:02}"

        # 문제 JSON 데이터 생성
        problem_data = {
            "question_id": question_id,
            "question": question,
            "question_plus": question_plus,
            "choices": choices,
            "answer": None,
            "score": None,
            "question_type": ""
        }
    
        problems.append(problem_data)

        problem_counter+=1

    # 섹션 JSON 데이터 생성
    section_data = {
        "id": section_id,
        "type": None,  # 기본값 설정
        "paragraph": paragraph,
        "paragraph_subject": "",  # 주제를 추가하려면 후처리 필요
        "problems": problems
    }

    result_data.append(section_data)

# JSON 파일 저장
with open(f"{json_path}{test_id}.json", "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=4)

# # 최종 json 결과 확인
# print(json.dumps(result_data, ensure_ascii=False, indent=4))


# %%
