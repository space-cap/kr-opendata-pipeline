# /// script
# dependencies = ["requests", "pymysql", "python-dotenv"]
# ///

import os
import logging
import math
import time
import argparse
from pathlib import Path

import pymysql
import requests
from dotenv import load_dotenv

# ==========================================
# 1. 로거 설정
# ==========================================
# 로그 폴더 생성
Path("logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),                          # 콘솔 출력
        logging.FileHandler("logs/collect_udi_master.log", encoding="utf-8"),  # 파일 저장
    ],
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. 환경 변수 로드 및 유효성 검사
# ==========================================
load_dotenv()

def _require_env(key: str) -> str:
    """필수 환경 변수가 없으면 즉시 종료합니다."""
    value = os.getenv(key)
    if not value:
        logger.critical(f"필수 환경 변수 '{key}'가 설정되지 않았습니다. .env 파일을 확인하세요.")
        raise SystemExit(1)
    return value

URL          = _require_env("UDI_API_URL")
DECODING_KEY = _require_env("UDI_API_KEY")
DB_HOST      = _require_env("DB_HOST")
DB_USER      = _require_env("DB_USER")
DB_PASSWORD  = _require_env("DB_PASSWORD")
DB_NAME      = _require_env("DB_NAME")

NUM_OF_ROWS   = 500
MAX_RETRIES   = 5       # API 최대 재시도 횟수
RETRY_DELAY   = 10      # 재시도 대기 시간 (초)
REQUEST_DELAY = 1.5     # 페이지 간 요청 간격 (초)
CHECKPOINT_FILE = "last_page.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==========================================
# 3. 유틸리티 함수
# ==========================================
def get_connection() -> pymysql.connections.Connection:
    """MariaDB 연결을 생성하고 반환합니다."""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        logger.info("MariaDB 연결 성공")
        return conn
    except pymysql.MySQLError as e:
        logger.critical(f"MariaDB 연결 실패: {e}")
        raise SystemExit(1)

def load_checkpoint() -> int:
    """파일에서 마지막으로 성공한 페이지 번호를 읽어옵니다."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        except Exception as e:
            logger.warning(f"체크포인트 파일을 읽는 중 오류 발생: {e}")
    return 1

def save_checkpoint(page: int):
    """마지막으로 성공한 페이지 번호를 파일에 기록합니다."""
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            f.write(str(page))
    except Exception as e:
        logger.error(f"체크포인트 파일 저장 실패: {e}")

# ==========================================
# 4. API 호출 함수 (최대 재시도 포함)
# ==========================================
def fetch_page(page_no: int) -> dict | None:
    """지정한 페이지의 API 응답을 반환합니다. 실패 시 None을 반환합니다."""
    params = {
        "serviceKey": DECODING_KEY,
        "pageNo":     str(page_no),
        "numOfRows":  str(NUM_OF_ROWS),
        "type":       "json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(URL, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()

            # API 자체 오류 코드 확인
            result_code = data.get("header", {}).get("resultCode", "")
            if result_code != "00":
                result_msg = data.get("header", {}).get("resultMsg", "알 수 없는 오류")
                logger.error(f"API 오류 응답 (페이지 {page_no}): [{result_code}] {result_msg}")
                return None

            return data

        except Exception as e:
            logger.warning(f"API 요청 실패 (페이지 {page_no}, {attempt}/{MAX_RETRIES}회 시도): {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"{RETRY_DELAY}초 후 재시도합니다...")
                time.sleep(RETRY_DELAY)

    logger.error(f"페이지 {page_no}를 {MAX_RETRIES}회 시도했으나 실패했습니다. 해당 페이지를 건너뜁니다.")
    return None

# ==========================================
# 5. 메인 수집 로직
# ==========================================
INSERT_SQL = """
    INSERT INTO mdv_udi_info (
        udidi_cd, prdlst_nm, clsf_grad_cd, prdt_nm_cont, biz_ipla_nm,
        mdeq_prdlst_sn, udi_modl_nm_sn, care_sal_trgt_yn,
        care_sal_cd_inpt_val, itgrt_info_reg_cmptn_dt
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) ON DUPLICATE KEY UPDATE
        prdlst_nm             = VALUES(prdlst_nm),
        clsf_grad_cd          = VALUES(clsf_grad_cd),
        prdt_nm_cont          = VALUES(prdt_nm_cont),
        biz_ipla_nm           = VALUES(biz_ipla_nm),
        mdeq_prdlst_sn        = VALUES(mdeq_prdlst_sn),
        udi_modl_nm_sn        = VALUES(udi_modl_nm_sn),
        care_sal_trgt_yn      = VALUES(care_sal_trgt_yn),
        care_sal_cd_inpt_val  = VALUES(care_sal_cd_inpt_val),
        itgrt_info_reg_cmptn_dt = VALUES(itgrt_info_reg_cmptn_dt)
"""

def run():
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="의료기기 UDI 마스터 정보 수집 스크립트")
    parser.add_argument("--start-page", type=int, help="수동으로 시작 페이지 지정")
    parser.add_argument("--no-checkpoint", action="store_true", help="체크포인트를 무시하고 1페이지부터 시작")
    args = parser.parse_args()

    # 시작 페이지 결정
    if args.start_page:
        current_page = args.start_page
        logger.info(f"명령줄 인자에 의해 {current_page}페이지부터 수집을 시작합니다.")
    elif args.no_checkpoint:
        current_page = 1
        logger.info("체크포인트를 무시하고 1페이지부터 수집을 시작합니다.")
    else:
        current_page = load_checkpoint()
        if current_page > 1:
            logger.info(f"이전 기록을 발견하여 {current_page}페이지부터 이어서 수집을 시작합니다.")
        else:
            logger.info("새로운 수집을 시작합니다 (1페이지).")

    connection = get_connection()
    total_inserted = 0

    try:
        with connection.cursor() as cursor:
            logger.info("🚀 UDI 마스터 데이터 대량 수집을 시작합니다!")

            while True:
                data = fetch_page(current_page)

                if data is None:
                    logger.error("데이터를 가져오지 못해 수집을 중단합니다.")
                    break

                body        = data.get("body", {})
                items       = body.get("items", [])
                total_count = body.get("totalCount", 0)

                if not items:
                    logger.info("✨ 더 이상 가져올 데이터가 없습니다. 수집 완료!")
                    break

                insert_data = [
                    (
                        item.get("UDIDI_CD"),
                        item.get("PRDLST_NM"),
                        item.get("CLSF_GRAD_CD"),
                        item.get("PRDT_NM_CONT"),
                        item.get("BIZ_IPLA_NM"),
                        item.get("MDEQ_PRDLST_SN"),
                        item.get("UDI_MODL_NM_SN"),
                        item.get("CARE_SAL_TRGT_YN"),
                        item.get("CARE_SAL_CD_INPT_VAL"),
                        item.get("ITGRT_INFO_REG_CMPTN_DT"),
                    )
                    for item in items
                ]

                cursor.executemany(INSERT_SQL, insert_data)
                connection.commit()

                total_inserted += len(items)
                total_pages = math.ceil(total_count / NUM_OF_ROWS)
                logger.info(
                    f"[{current_page}/{total_pages} 페이지] "
                    f"{len(items)}건 저장 완료 (누적: {total_inserted:,}/{total_count:,})"
                )

                # 체크포인트 저장 (현재 페이지 성공)
                save_checkpoint(current_page)

                current_page += 1
                time.sleep(REQUEST_DELAY)

    except KeyboardInterrupt:
        logger.warning("사용자에 의해 강제 종료되었습니다.")
    except Exception as e:
        logger.exception(f"치명적인 시스템 에러: {e}")
    finally:
        connection.close()
        logger.info("DB 연결을 안전하게 종료했습니다.")


if __name__ == "__main__":
    run()