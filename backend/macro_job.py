import pandas as pd
import requests
from datetime import datetime
import os
from google.cloud import firestore
from pathlib import Path

# Get the directory where the current script (macro_job.py) is located
current_dir = Path(__file__).parent
# Construct the path to the key file within the same directory
firestore_key_path = current_dir / "firestore-key.json"

# Initialize Firestore client using the correct path
# Ensure the path is converted to a string for the function
try:
    db = firestore.Client.from_service_account_json(str(firestore_key_path))
except FileNotFoundError:
    print(f"ERROR: Firestore key file not found at {firestore_key_path}")
    db = None # Set db to None if key is not found to prevent further errors
except Exception as e:
    print(f"ERROR: Failed to initialize Firestore client: {e}")
    db = None


# Removed 'self' parameter and corrected db access
def get_macro_document():
    if not db:
        print("ERROR: Firestore client not initialized. Cannot get document.")
        return None
    user_doc = db.collection("users").document('ramus') # Use global 'db'
    today = datetime.now().strftime("%Y-%m-%d")
    document = user_doc.collection('macro_economics').document(today)
    return document

# Removed 'self' parameter
def save_macro_economics_data(document):
        """
        "FEDFUNDS",  # 연방 기금 금리
        "DGS10",     # 10년 만기 국채 금리
        "CPIAUCNS",  # 소비자 물가 지수
        "PCEPI",     # 개인 소비 지출 물가 지수
        "PPIACO",    # 생산자 물가 지수
        "GDPC1",     # 실질 국내총생산
        "UNRATE",    # 실업률
        "M2SL",      # M2 (광의 통화량)
        "INDPRO",    # 산업 생산 지수
        "UMCSENT",   # 미시간 대학교 소비자 심리 지수
        "T10Y2Y",    # 장단기 금리차
        "VIXCLS",    # 공포지수
        "PAYEMS",    # 비농업 부문 고용자 수 
        "HOUST",     # 주택 판매 지수
        "CPILFENS",  # 미국 도시지역 소비자물가지수 중 식품과 에너지를 제외한 “Core CPI”
        "ICSA",      # 초기 실업수당 청구건수
        "BAMLC0A0CM" # 회사채 스프레드를 나타내는 Series ID 
        "SP500"      # S&P 500 지수
        """
        # 가져올 데이터 시리즈 ID 목록
        series_ids = [
            "FEDFUNDS", "DGS10", "CPIAUCNS", "PCEPI", "PPIACO", "GDPC1",
            "UNRATE", "M2SL", "INDPRO", "UMCSENT", "T10Y2Y", "VIXCLS", "PAYEMS", "HOUST",
            "CPILFENS", "ICSA", "BAMLC0A0CM", "SP500"
        ]
        # FRED API 키 (본인의 키로 변경)
        api_key = os.environ["FRED_API_KEY"]
        # 데이터 요청 종료 날짜 (오늘 날짜로 설정)
        end_date = datetime.now().strftime("%Y-%m-%d")

        # 데이터 요청 시작 날짜 (최근 1년으로 설정, 필요에 따라 조절 가능)
        start_date = (datetime.now() - pd.DateOffset(months=6)).strftime("%Y-%m-%d")

        all_data = {}

        for series_id in series_ids:
            try:
                # observations API 호출 (최신 데이터만 가져오도록 범위 지정)
                observations_url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&observation_start={start_date}&observation_end={end_date}"
                response = requests.get(observations_url).json()
                observations = response.get("observations")

                if observations:
                    # dates = [obs["date"] for obs in observations]
                    # values = [float(obs["value"]) if obs["value"] != "." and obs["value"] is not None else None for obs in observations]
                    all_data[series_id] = [{"date": obs["date"], "value": float(obs["value"]) if obs["value"] != "." and obs["value"] is not None else None} for obs in observations]  # List of dictionaries
                    # all_data[series_id] = pd.Series(values, index=pd.to_datetime(dates))
                else:
                    print(f"No observations found for {series_id}")

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data for {series_id}: {e}")
            except (KeyError, IndexError) as e:
                print(f"Error parsing JSON for {series_id}: {e}")

        document.set(all_data)

# background 에서 하루에 한번 실행
def save_macro_economics():
    if not db:
        print("ERROR: Firestore client not initialized. Skipping macro economics save.")
        return

    document = get_macro_document()
    if document and not document.get().exists:
        print(f"INFO: Macro economics data for today does not exist. Saving...")
        save_macro_economics_data(document)
        print(f"INFO: Macro economics data saved.")
    elif document:
        print(f"INFO: Macro economics data for today already exists. Skipping save.")
    else:
        print("ERROR: Could not get Firestore document. Skipping macro economics save.")
