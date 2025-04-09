#main.py (backend)

import os
import json
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama
from src.prompt import prompts
from dotenv import load_dotenv

from typing import Optional, Dict
from langchain_core.tools import tool
from typing import Annotated
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain.globals import set_verbose, set_debug
set_verbose(True)
set_debug(True)

from db import PostgreSqlDB
import db_sql
import src.agent_prompt as agent_prompt

# ---------------------------
# DATA MODELS & CONVERSATION STATE
# ---------------------------
class UserQuery(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    current_step: Optional[str] = None

class ConversationState:
    def __init__(self):
        self.conversations: Dict[str, dict] = {}

    def get_conversation(self, conv_id: str) -> dict:
        if conv_id not in self.conversations:
            self.conversations[conv_id] = self.create_new_conversation()
        return self.conversations[conv_id]

    def create_new_conversation(self) -> dict:
        print("###########LOG#############: create new conversation. created")
        return {
            "intent": None,
            "current_step": None,
            "context": {},
            "history": [],
            "pending_intent": None
        }

    def reset_conversation(self, conv_id: str):
        self.conversations[conv_id] = self.create_new_conversation()

    def update_conversation(self, conv_id: str, intent: Optional[str] = None,
                            current_step: Optional[str] = None,
                            context: Optional[dict] = None,
                            history: Optional[list] = None):
        conv = self.get_conversation(conv_id)
        if intent is not None:
            conv["intent"] = intent
        if current_step is not None:
            conv["current_step"] = current_step
        if context:
            conv["context"].update(context)
        if history:
            conv["history"].extend(history)

# ---------------------------
# INITIALIZATION
# ---------------------------
load_dotenv()
app = FastAPI()
conversation_state = ConversationState()

# Since PostgreSqlDB does not accept connection parameters in the constructor,
# we simply instantiate it. (Make sure your PostgreSqlDB reads connection details
# from environment variables or is configured accordingly.)

# dsn = (
#     f"host={os.getenv('DB_HOST', '141.164.46.113')} "
#     f"port={os.getenv('DB_PORT', '5432')} "
#     f"dbname={os.getenv('DB_NAME', 'smarthomedb2')} "
#     f"user={os.getenv('DB_USER', 'abcd')} "
#     f"password={os.getenv('DB_PASSWORD', '1234')}"
# )

       


postrgre_db = PostgreSqlDB()


# LLM initialization – using a smaller model for testing purposes.
llm = ChatOllama(model="mistral-small:latest")
#llm = ChatOllama(model="gemma3:1b")
#deepseek-r1:8b
#gemma3:1b 
 
# llm = ChatOllama(model="jinbora/deepseek-r1-Bllossom:8b")

origins = [
    "http://61.108.166.15",
    "http://61.108.166.15:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

human = """
{input}

{agent_scratchpad}

(reminder to respond in a JSON blob no matter what)
"""

# ---------------------------
# TOOL DEFINITIONS
# ---------------------------


@tool
def add_medicine(
    medication: Annotated[str, "추가할 약 이름 (예: 타이레놀)"],
    schedule: Annotated[str, "복용 스케줄 정보 (예: 매일 아침, 아침 점심 저녁)"],
    total_amount: Annotated[str, "복용약 총량 (예: 7, 30)"]
) -> str:
    """
    약 추가 기능

    이 함수는 약 이름과 복용 스케줄 정보를 받아서, 데이터베이스의 캐비닛 테이블에서
    사용 가능한 슬롯(소켓)을 찾은 후, 해당 슬롯을 업데이트하여 약 정보를 저장합니다.
    업데이트 시 'taken' 컬럼 및 기타 관련 정보를 함께 갱신합니다.
    """
    try:
        # 1. 사용 가능한 캐비닛 슬롯(소켓)을 찾습니다.
        empty_cabinet = postrgre_db.fetch_one(db_sql.select_empty_cabinet)
        if empty_cabinet is None:
            return "사용 가능한 캐비닛 슬롯이 없습니다. 먼저 기존 항목을 제거해주세요. 더 필요하신 사항이 있으시면 말씀해주세요. "
        box_num = empty_cabinet.get("box_num")
        
        # 2. schedule 문자열에 기반하여 각 복용 시간(아침, 점심, 저녁) 플래그를 설정합니다.
        lines = schedule.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # First, try splitting by comma. If only one token is found and it has spaces, split by whitespace.
            tokens = [token.strip() for token in line.split(',') if token.strip()]
            if len(tokens) == 1 and " " in tokens[0]:
                tokens = tokens[0].split()
            if not tokens:
                continue

            # Define your scheduling keywords as a regex pattern:
            pattern = re.compile(r"(아침|점심|저녁|중식|세번|두번|한번|하루|서번|세)")

            # Instead of splitting the line, search directly:
            scheduling_tokens = pattern.findall(schedule.replace(" ", ""))


            # Process scheduling tokens for flags.
            breakfast = lunch = dinner = 0
            for token in scheduling_tokens:
                # If token contains "세번" or "서번", set all scheduling flags.
                if "세번" in token or "서번" in token:
                    breakfast, lunch, dinner = 1, 1, 1
                elif "두번" in token or "두 번" in token:
                    breakfast, dinner = 1, 1
                if "아침" in token:
                    breakfast = 1
                if "점심" in token or "중식" in token:
                    lunch = 1
                if "저녁" in token:
                    dinner = 1
                if "한번" in token and not (breakfast or lunch or dinner):
                    breakfast = 1
                # We ignore "하루" here as it is redundant.        
        
        # breakfast = 1 if "아침" in schedule else 0
        # lunch = 1 if ("점심" in schedule or "중식" in schedule) else 0
        # dinner = 1 if "저녁" in schedule else 0
        breakfast_val = int(breakfast)
        lunch_val = int(lunch)
        dinner_val = int(dinner)  # Even if dinner is False, int(False) yields 0.

        # 3. 각 시간별 상태 문자열 설정
        breakfast_status = 0 
        lunch_status = 0 
        dinner_status = 0 

        print(f"breakfast: {breakfast_val}, lunch: {lunch_val}, dinner: {dinner_val}")
                
        medicine_bool = True   # 약 관련 여부
        taken = True           # 슬롯이 사용 중임을 표시
        
        # 4. 캐비닛 슬롯(소켓)을 업데이트합니다.
        postrgre_db.execute(
            db_sql.update_cabinet,
            (
                medication,      # name
                taken,           # taken 컬럼
                medicine_bool,   # medicine_bool
                total_amount,    # total_amount
                breakfast_val,     # breakfast 플래그
                lunch_val,       # lunch 플래그
                dinner_val,      # breakfast 컬럼에 dinner 플래그 (테이블 구조에 따라 조정)
                breakfast_status,  # breakfast_status
                lunch_status,    # lunch_status
                dinner_status,   # dinner_status
                box_num          # 업데이트할 캐비닛 번호            
            )
        )
        return f"{medication}이 {box_num}번 보관함에 {schedule} 스케쥴로 추가되었습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
    except Exception as e:
        return f"약 추가 중 오류 발생: {e}"

@tool
def remove_medicine(
    cabinet_number: Annotated[Optional[str], "삭제할 보관함 번호 (예: 1번). 제공하지 않으면, 약 이름으로 검색합니다."] = "",
    medicine: Annotated[Optional[str], "삭제할 약 이름 (예: 타이레놀, 혈압약). 보관함 번호를 모를 때 사용합니다."] = ""
) -> str:
    """
    약 삭제 기능

    이 함수는 사용자가 입력한 약 이름을 우선 검색하고, 
    약 이름이 제공되지 않을 경우 보관함 번호로 검색하여 해당 보관함 슬롯의 내용을 삭제합니다.
    업데이트 시 'taken' 컬럼 및 기타 관련 정보를 초기 상태로 복원합니다.
    """
    try:
        # 먼저, 약 이름이 제공되었는지 확인합니다.
        if medicine:
            row = postrgre_db.fetch_one(db_sql.select_cabinet_by_medicine, (medicine,))
            if row is None:
                return f"입력한 약 '{medicine}'을(를) 찾을 수 없습니다."
            box_num = row.get("box_num")
        # 만약 약 이름이 없고 보관함 번호가 제공되었다면, 해당 번호를 사용합니다.
        elif cabinet_number:
            box_num = cabinet_number
        else:
            return "삭제할 보관함 번호나 약 이름을 제공해주세요."

        # 디버그 출력: 삭제할 보관함 번호 확인
        print(f"Deleting contents of cabinet slot: {box_num}")

        # 주의: 사용 중인 SQL 쿼리 이름이 실제로 'remove_cabinet_contents'라면,
        # 아래의 함수 호출에서도 같은 이름을 사용해야 합니다.
        postrgre_db.execute(db_sql.remove_cabinet_contents, (box_num,))
        return f"보관함 번호 {box_num}의 약이 성공적으로 삭제되었습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
    except Exception as e:
        return f"약 삭제 중 오류 발생: {e}"

@tool
def check_schedule(
    cabinet_number: Annotated[Optional[str], "스케쥴 체크할 보관함 번호 (예: 1번). 제공하지 않으면, 약 이름으로 검색합니다."] = "",
    medicine: Annotated[Optional[str], "스케쥴 체크할 약 이름 (예: 타이레놀, 혈압약). 보관함 번호를 모를 때 사용합니다."] = ""
) -> str:
    """
    약 스케쥴 확인 기능

    이 함수는 사용자가 입력한 약 이름을 우선 검색하고,
    약 이름이 제공되지 않을 경우 보관함 번호로 검색하여 해당 보관함 슬롯의 약 스케쥴 정보를 조회합니다.
    조회된 정보를 바탕으로, 약이 어느 보관함에 있으며, 어느 시간대에 복용해야 하는지,
    남은 약량(예: 일치), 그리고 오늘 각 복용시간별 복용 여부를 설명하는 문장을 반환합니다.
    """
    try:
        # Determine cabinet slot based on medicine name or provided cabinet number.
        if medicine:
            row = postrgre_db.fetch_one(db_sql.select_cabinet_by_medicine, (medicine,))
            if row is None:
                return f"입력한 약 '{medicine}'을(를) 찾을 수 없습니다."
            box_num = row.get("box_num")
        elif cabinet_number:
            box_num = cabinet_number
        else:
            return "보관함 번호나 약 이름을 제공해주세요."

        print(f"Checking schedule of cabinet slot: {box_num}")

        # Retrieve schedule information.
        # Ensure your SQL query (e.g. select_medicine_schedule) returns the following fields:
        # name, box_num, breakfast, lunch, dinner,
        # total_amount, today_breakfast_taken, today_lunch_taken, today_breakfast_taken
        schedule_row = postrgre_db.fetch_one(db_sql.select_cabinet_by_box, (box_num,))
        if schedule_row is None:
            return f"보관함 번호 {box_num}의 약 정보가 존재하지 않습니다. 더 필요하신 사항이 있으시면 말씀해주세요."

        # Extract values.
        med_name = schedule_row.get("name") or "해당 약"
        breakfast_flag = int(schedule_row.get("breakfast", 0))
        lunch_flag = int(schedule_row.get("lunch", 0))
        dinner_flag = int(schedule_row.get("dinner", 0))  # 'breakfast' column used for dinner
        total_amount = schedule_row.get("total_amount")
        # For today's intake statuses, assume boolean or values convertible to bool.
        today_breakfast_taken = schedule_row.get("breakfast_status", 0)
        today_lunch_taken = schedule_row.get("lunch_status", 0)
        today_dinner_taken = schedule_row.get("dinner_status", 0)

        # Build scheduled times string.
        scheduled_times = []
        if breakfast_flag:
            scheduled_times.append("아침")
        if lunch_flag:
            scheduled_times.append("점심")
        if dinner_flag:
            scheduled_times.append("저녁")
        if not scheduled_times:
            scheduled_str = "복용 스케쥴이 지정되어 있지 않습니다."
        else:
            scheduled_str = " ".join(scheduled_times) + "으로 복용하고 계십니다."

        # Build today's intake status string.
        intake_status_parts = []
        if breakfast_flag:
            status = "드셨습니다" if today_breakfast_taken else "아직 안드셨습니다"
            intake_status_parts.append(f"아침약은 {status}")
        if lunch_flag:
            status = "드셨습니다" if today_lunch_taken else "아직 안드셨습니다"
            intake_status_parts.append(f"점심약은 {status}")
        if dinner_flag:
            status = "드셨습니다" if today_dinner_taken else "아직 안드셨습니다"
            intake_status_parts.append(f"저녁약은 {status}")
        intake_status_str = " , ".join(intake_status_parts)

        # Build remaining amount string.
        remaining_str = f"현재 약은 {total_amount}일치가 남아있습니다." if total_amount is not None else ""

        # Combine into final message.
        final_message = (
            f"{med_name}은 {box_num}번 보관함에 보관되어 있으며, {scheduled_str} "
            f"{remaining_str} 오늘 {intake_status_str}."
            f"더 필요하신 사항이 있으시면 말씀해주세요."
        )
        return final_message
    except Exception as e:
        return f"약 스케쥴 확인 중 오류 발생: {e}"

@tool
def add_thing(
    thing_name: Annotated[str, "추가할 물건 이름 (예: 우산, 열쇠)"],
) -> str:
    """
    물건 추가 기능

    이 함수는 물건 이름을 받아서,
    데이터베이스의 보관함 테이블에서 사용 가능한 보관함을 찾은 후,
    해당 보관함을 업데이트하여 물건 정보를 저장합니다.
    
    물건 추가 시:
    - medicine_bool은 false로 설정됩니다.
    - total_amount는 0으로 설정됩니다.
    - 아침, 점심, 저녁 플래그 모두 0으로 설정됩니다.
    - 각 시간별 상태는 '0'으로 설정됩니다.
    """
    try:
        empty_cabinet = postrgre_db.fetch_one(db_sql.select_empty_cabinet)
        if empty_cabinet is None:
            return "사용 가능한 캐비닛 슬롯이 없습니다. 먼저 기존 항목을 제거해주세요. 더 필요하신 사항이 있으시면 말씀해주세요."
        cabinet_number = empty_cabinet.get("box_num")      # Update the cabinet row with thing data.
        postrgre_db.execute(
            db_sql.update_cabinet,
            (
                thing_name,      # name: store thing name
                True,            # taken becomes True
                False,           # medicine_bool is false for things
                0,               # total_amount is 0
                0,               # breakfast flag = 0
                0,               # lunch flag = 0
                0,               # breakfast (dinner) flag = 0
                0,     # breakfast_status
                0,     # lunch_status
                0,     # dinner_status
                cabinet_number   # cabinet number
            )
        )
        return f"{thing_name}이(가) {cabinet_number}번 보관함에 추가되었습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
    except Exception as e:
        return f"물건 추가 중 오류 발생: {e}"


@tool
def remove_thing(
    cabinet_number: Annotated[Optional[str], "삭제할 보관함 번호 (예: 1번). 제공하지 않으면, 물건 이름으로 검색합니다."] = "",
    thing_name: Annotated[Optional[str], "삭제할 물건 이름 (예: 우산, 열쇠). 보관함 번호를 모를 때 사용합니다."] = ""
) -> str:
    """
    물건 삭제 기능

    이 함수는 사용자가 입력한 물건 이름을 우선 검색하고,
    물건 이름이 제공되지 않을 경우 보관함 번호로 검색하여 해당 보관함 슬롯의 내용을 삭제(초기화)합니다.
    
    삭제 시, 해당 슬롯은 기본 상태(비사용 상태)로 복원됩니다.
    """
    try:
        if thing_name:
            row = postrgre_db.fetch_one(db_sql.select_cabinet_by_medicine, (thing_name,))
            if row is None:
                return f"입력한 물건 '{thing_name}'을(를) 찾을 수 없습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
            cabinet_number = row.get("box_num")
        elif cabinet_number:
            row = postrgre_db.fetch_one(db_sql.select_cabinet_by_box, (cabinet_number,))
            if row is None:
                return f"보관함 번호 {cabinet_number}가 존재하지 않습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
        else:
            return "삭제할 보관함 번호나 물건 이름을 제공해주세요.더 필요하신 사항이 있으시면 말씀해주세요."
        print(f"Deleting contents of cabinet slot: {cabinet_number}")
        postrgre_db.execute(db_sql.remove_cabinet_contents, (cabinet_number,))
        return f"보관함 번호 {cabinet_number}의 물건이 성공적으로 삭제되었습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
    except Exception as e:
        return f"물건 삭제 중 오류 발생: {e}"

# @tool
# def describe_thing(
# ) -> str:
#     """
#     물건 삭제 기능

#     이 함수는 사용자가 입력한 물건 이름을 우선 검색하고,
#     물건 이름이 제공되지 않을 경우 보관함 번호로 검색하여 해당 보관함 슬롯의 내용을 삭제(초기화)합니다.
    
#     삭제 시, 해당 슬롯은 기본 상태(비사용 상태)로 복원됩니다.
#     """
#     try:
#         if thing_name:
#             row = postrgre_db.fetch_one(db_sql.select_cabinet_by_medicine, (thing_name,))
#             if row is None:
#                 return f"입력한 물건 '{thing_name}'을(를) 찾을 수 없습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
#             cabinet_number = row.get("box_num")
#         elif cabinet_number:
#             row = postrgre_db.fetch_one(db_sql.select_cabinet_by_box, (cabinet_number,))
#             if row is None:
#                 return f"보관함 번호 {cabinet_number}가 존재하지 않습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
#         else:
#             return "삭제할 보관함 번호나 물건 이름을 제공해주세요.더 필요하신 사항이 있으시면 말씀해주세요."
#         print(f"Deleting contents of cabinet slot: {cabinet_number}")
#         postrgre_db.execute(db_sql.remove_cabinet_contents, (cabinet_number,))
#         return f"보관함 번호 {cabinet_number}의 물건이 성공적으로 삭제되었습니다. 더 필요하신 사항이 있으시면 말씀해주세요."
#     except Exception as e:
#         return f"물건 삭제 중 오류 발생: {e}"

# ---------------------------
# AGENT INITIALIZATION
# ---------------------------


memory = ConversationBufferMemory(
    memory_key="chat_history",
    output_key="output",  # 출력 키 명시적 설정
    return_messages=True
)


#For add_medicine
add_medicine_agent = create_structured_chat_agent(
    llm,
    [add_medicine],
    ChatPromptTemplate.from_messages(
        [
            ("system", agent_prompt.search_prompt_medication_add),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human)
        ]
    )
)

add_medicine_agent_executor = AgentExecutor(
    agent=add_medicine_agent,
    tools=[add_medicine],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

#For delete_medicine
remove_medicine_agent = create_structured_chat_agent(
    llm,
    [remove_medicine],
    ChatPromptTemplate.from_messages(
        [
            ("system", agent_prompt.search_prompt_medication_remove),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human)
        ]
    )
)

remove_medicine_agent_executor = AgentExecutor(
    agent=remove_medicine_agent,
    tools=[remove_medicine],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

#For check_schedule
check_schedule_agent = create_structured_chat_agent(
    llm,
    [check_schedule],
    ChatPromptTemplate.from_messages(
        [
            ("system", agent_prompt.search_prompt_check_schedule),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human)
        ]
    )
)

check_schedule_agent_executor = AgentExecutor(
    agent=check_schedule_agent,
    tools=[check_schedule],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

# For add_thing
add_thing_agent = create_structured_chat_agent(
    llm,
    [add_thing],
    ChatPromptTemplate.from_messages(
        [
            ("system", agent_prompt.search_prompt_thing_add), 
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human)
        ]
    )
)

add_thing_agent_executor = AgentExecutor(
    agent=add_thing_agent,
    tools=[add_thing],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

# For remove_thing
remove_thing_agent = create_structured_chat_agent(
    llm,
    [remove_thing],
    ChatPromptTemplate.from_messages(
        [
            ("system", agent_prompt.search_prompt_medication_remove), 
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human)
        ]
    )
)

remove_thing_agent_executor = AgentExecutor(
    agent=remove_thing_agent,
    tools=[remove_thing],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

# For remove_thing
# describe_thing_agent = create_structured_chat_agent(
#     llm,
#     [describe_thing],
#     ChatPromptTemplate.from_messages(
#         [
#             ("system", agent_prompt.search_prompt_thing_describe), 
#             MessagesPlaceholder("chat_history", optional=True),
#             ("human", human)
#         ]
#     )
# )

# describe_thing_agent_executor = AgentExecutor(
#     agent=describe_thing_agent,
#     tools=[describe_thing],
#     handle_parsing_errors=True,
#     memory=memory,
#     max_iterations=7,
# )
##########################
#딕셔너리
chain_intent = {        # 체인 정의 (중간 의도 파악용, 답변 활용X)
    "INTENT"                    :   prompts["intent_classifier_0"]                  | llm | StrOutputParser(),  # 기본 의도 파악
 }

chains_prompt = {       # 체인 정의 (답변용)
    "GREETING"              :   prompts["greeting_0"]               | llm | StrOutputParser(), # 단순인사 prompt
    "GENERAL_INQUIRIES"     :   prompts["general_inquiries"]        | llm | StrOutputParser()
}

str_MEDICATION_ACTIONS = {
    "CHECK_TODAY_MEDICATION_STATUS": "오늘 복용 확인을",
    "EXPLAIN_MEDICATION_SCHEDULE":  "약 복용 스케줄 설명을",
    "ADD_MEDICINE":                "약 추가를",
    "REMOVE_MEDICINE":             "약 삭제를",
    "ADD_MEDICATION_SCHEDULE":     "약 복용 스케줄 추가를",
    "ADD_THING":                   "물건 추가를",
    "REMOVE_THING":                "물건 삭제를",
    "DESCRIBE_THING":              "물건 설명을",
    "CHECK_SOCKET_ITEM":           "보관함 내 항목 확인을",
    "EXPLAIN_CABINET_CONTENTS":    "보관함 내용 설명을"
}

answers_nollm = {
    "REASK"                 :   "죄송합니다. 질문을 이해하지 못했습니다. 이전 문의하신 내용을 계속 진행하시겠습니까?",
    "NEWASK"                :   "주인님 안녕하세요! 약손입니다. 더 필요하신 사항이 있으시면 말씀해주세요. \n 약스케쥴, 약추가, 약삭제, 물건추가, 물건삭제, 물건묘사"
}



# ---------------------------
# CHAT ENDPOINT
# ---------------------------
@app.post("/chat/")
async def chat(query: UserQuery):
    try:
        conv = conversation_state.get_conversation(query.conversation_id)
        previous_intent = conv["intent"]
        previous_step = conv["current_step"]
        answer = None
        print(" conv : ", conv)
        print("previous_intent : ", previous_intent)
        print("previous_step : ", previous_step)
        print("answer : ", answer)
        
        # 1. Intent Classification
        if not conv["intent"]:
            intent = chain_intent["INTENT"].invoke({"question": query.question}).strip()
            dict_list = [chain_intent, chains_prompt, str_MEDICATION_ACTIONS]
            if intent in ["ADD_MEDICINE", "REMOVE_MEDICINE", "CHECK_SCHEDULE", "ADD_THING", "REMOVE_THING", "DESCRIBE_THING"]:
                context = {
                    "question": query.question,
                    "current_step": conv["current_step"],
                    "context": json.dumps(conv["context"]),
                }
                if intent in ["ADD_MEDICINE", "REMOVE_MEDICINE", "CHECK_SCHEDULE", "ADD_THING", "REMOVE_THING", "DESCRIBE_THING"]:
                    conv["intent"] = intent
                else:
                    intent = "None"
            if "None" in intent or not any(intent in d for d in dict_list):
                if previous_intent:
                    answer = answers_nollm["REASK"]
                    conv["intent"] = previous_intent
                    conv["current_step"] = previous_step
                    conv["is_reset"] = False
                else:
                    answer = answers_nollm["NEWASK"]
                    conv["intent"] = None
                    conv["current_step"] = None
                    conv["is_reset"] = True
            conv["intent"] = intent

        # 2. Answer Generation based on intent
        # We'll separate branches to ensure that the tool output is used directly.
        if conv.get("intent", "") == "ADD_MEDICINE":
            chat_history = memory.buffer_as_messages
            if conv["current_step"] is None:
                response = add_medicine_agent_executor.invoke({
                    "input": query.question,
                    "chat_history": chat_history,
                })
            print(response)
            answer = (response.get('output') or "").strip()
            if "더 필요하신" in response['output']:   
                conv["current_step"] = None
                conv["intent"] = ""    
            if not answer:
                answer = "죄송합니다, 문제가 발생했습니다. 다른 질문을 해주시거나 다시 시도해주세요."
            
        elif conv.get("intent", "") == "REMOVE_MEDICINE":
            chat_history = memory.buffer_as_messages
            if conv["current_step"] is None:
                response = remove_medicine_agent_executor.invoke({
                    "input": query.question,
                    "chat_history": chat_history,
                })
            print(response)
            answer = (response.get('output') or "").strip()
            if "더 필요하신" in response['output']:   # intent 초기화 ################# prompt에 intent 종료 시그널 포함시켜야 됨.
                conv["current_step"] = None
                conv["intent"] = ""    
            if not answer:
                answer = "죄송합니다, 문제가 발생했습니다. 다른 질문을 해주시거나 다시 시도해주세요."

        elif conv.get("intent", "") == "CHECK_SCHEDULE":
            chat_history = memory.buffer_as_messages
            if conv["current_step"] is None:
                response = check_schedule_agent_executor.invoke({
                    "input": query.question,
                    "chat_history": chat_history,
                })
            print(response)
            answer = (response.get('output') or "").strip()
            if "더 필요하신" in response['output']:   # intent 초기화 ################# prompt에 intent 종료 시그널 포함시켜야 됨.
                conv["current_step"] = None
                conv["intent"] = ""    
            if not answer:
                answer = "죄송합니다, 문제가 발생했습니다. 다른 질문을 해주시거나 다시 시도해주세요."

        elif conv.get("intent", "") == "ADD_THING":
            chat_history = memory.buffer_as_messages
            if conv["current_step"] is None:
                response = add_thing_agent_executor.invoke({
                    "input": query.question,
                    "chat_history": chat_history,
                })
            print(response)
            answer = (response.get('output') or "").strip()
            if "더 필요하신" in response['output']:   # intent 초기화 ################# prompt에 intent 종료 시그널 포함시켜야 됨.
                conv["current_step"] = None
                conv["intent"] = ""  
            if not answer:
                answer = "죄송합니다, 문제가 발생했습니다. 다른 질문을 해주시거나 다시 시도해주세요."

        elif conv.get("intent", "") == "REMOVE_THING":
            chat_history = memory.buffer_as_messages
            if conv["current_step"] is None:
                response = remove_thing_agent_executor.invoke({
                    "input": query.question,
                    "chat_history": chat_history,
                })
            print(response)
            answer = (response.get('output') or "").strip()
            if "더 필요하신" in response['output']:   # intent 초기화 ################# prompt에 intent 종료 시그널 포함시켜야 됨.
                conv["current_step"] = None
                conv["intent"] = ""  
            if not answer:
                answer = "죄송합니다, 문제가 발생했습니다. 다른 질문을 해주시거나 다시 시도해주세요."
        
        elif conv.get("intent", "") == "DESCRIBE_THING":
            conv["current_step"] = None
            conv["intent"] = ""  
            return {
                "answer": "물건을 분석하는 중입니다 잠시만 기다려주세요",
                "intent": "DESCRIBE_THING",
                "current_step": conv.get("current_step"),
                "is_reset": conv.get("intent") is None,  # or use another flag as needed
                "context": conv.get("context", {})
        }

        # 3. Update conversation history
        conversation_state.update_conversation(
            query.conversation_id,
            history=[{"question": query.question, "answer": answer, "step": conv.get("current_step")}]
        )
        
        return {
            "answer": answer,
            "intent": conv.get("intent"),
            "current_step": conv.get("current_step"),
            "is_reset": conv.get("intent") is None,  # or use another flag as needed
            "context": conv.get("context", {})
        }
    
    except Exception as e:
        print(e)
        return {"error": str(e)}
