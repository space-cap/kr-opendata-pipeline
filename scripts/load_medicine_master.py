import os
import logging
import argparse
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv

# ==========================================
# 1. 로거 설정
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("load_medicine_master.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. 환경 변수 로드 및 유효성 검사
# ==========================================
load_dotenv()

def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        logger.critical(f"필수 환경 변수 '{key}'가 설정되지 않았습니다. .env 파일을 확인하세요.")
        raise SystemExit(1)
    return value

DB_HOST     = _require_env("DB_HOST")
DB_USER     = _require_env("DB_USER")
DB_PASSWORD = _require_env("DB_PASSWORD")
DB_NAME     = _require_env("DB_NAME")

BATCH_SIZE  = 1000  # 한 번에 DB에 저장할 행 수

# ==========================================
# 3. 유틸리티 함수
# ==========================================
def get_connection() -> pymysql.connections.Connection:
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

def parse_date(val: str) -> str | None:
    """'YYYYMMDD' 형식의 날짜를 'YYYY-MM-DD'로 변환합니다.
    비어있거나 존재하지 않는 날짜(예: 11월 31일)면 None 반환."""
    val = val.strip()
    if val and len(val) == 8 and val.isdigit():
        try:
            dt = datetime.strptime(val, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"유효하지 않은 날짜 발견, NULL로 저장: '{val}'")
            return None
    return None

def to_none(val: str) -> str | None:
    """빈 문자열을 None(DB의 NULL)으로 변환합니다."""
    stripped = val.strip()
    return stripped if stripped else None

def to_int(val: str) -> int:
    """정수로 변환합니다. 실패하면 0 반환."""
    try:
        return int(val.strip())
    except (ValueError, AttributeError):
        return 0

# ==========================================
# 4. SQL
# ==========================================
# 원본 파일의 컬럼 순서:
# 한글상품명|업체명|약품규격|제품총수량|제형구분|포장형태|
# 품목기준코드|품목허가일자|전문/일반|대표코드|표준코드|제품코드(개정후)|
# 일반명코드(성분명코드)|비고|취소일자|양도양수적용(공고)일자|양도양수종료일자|
# 일련번호생략여부|일련번호생략사유|ATC코드|특수관리약품구분|의약품판독장비구분

INSERT_SQL = """
    INSERT INTO medicine_master (
        std_code, product_name, company_name, spec, total_qty,
        formulation_type, package_type, item_std_code, approval_date,
        med_category, rep_code, revised_code, generic_code, remarks,
        cancel_date, transfer_apply_date, transfer_end_date,
        serial_omit_yn, serial_omit_reason, atc_code,
        special_mgmt_type, reader_device_type
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s
    ) ON DUPLICATE KEY UPDATE
        product_name        = VALUES(product_name),
        company_name        = VALUES(company_name),
        spec                = VALUES(spec),
        total_qty           = VALUES(total_qty),
        formulation_type    = VALUES(formulation_type),
        package_type        = VALUES(package_type),
        item_std_code       = VALUES(item_std_code),
        approval_date       = VALUES(approval_date),
        med_category        = VALUES(med_category),
        rep_code            = VALUES(rep_code),
        revised_code        = VALUES(revised_code),
        generic_code        = VALUES(generic_code),
        remarks             = VALUES(remarks),
        cancel_date         = VALUES(cancel_date),
        transfer_apply_date = VALUES(transfer_apply_date),
        transfer_end_date   = VALUES(transfer_end_date),
        serial_omit_yn      = VALUES(serial_omit_yn),
        serial_omit_reason  = VALUES(serial_omit_reason),
        atc_code            = VALUES(atc_code),
        special_mgmt_type   = VALUES(special_mgmt_type),
        reader_device_type  = VALUES(reader_device_type)
"""

# ==========================================
# 5. 데이터 파싱 함수
# ==========================================
def parse_row(cols: list[str]) -> tuple:
    """파이프로 분리된 컬럼 리스트를 DB INSERT용 튜플로 변환합니다."""
    # 원본 컬럼 순서에 맞게 인덱스 매핑
    product_name        = to_none(cols[0])   # 한글상품명
    company_name        = to_none(cols[1])   # 업체명
    spec                = to_none(cols[2])   # 약품규격
    total_qty           = to_int(cols[3])    # 제품총수량
    formulation_type    = to_none(cols[4])   # 제형구분
    package_type        = to_none(cols[5])   # 포장형태
    item_std_code       = to_none(cols[6])   # 품목기준코드
    approval_date       = parse_date(cols[7])# 품목허가일자
    med_category        = to_none(cols[8])   # 전문/일반
    rep_code            = to_none(cols[9])   # 대표코드
    std_code            = to_none(cols[10])  # 표준코드 (UNIQUE KEY)
    revised_code        = to_none(cols[11])  # 제품코드(개정후)
    generic_code        = to_none(cols[12])  # 일반명코드
    remarks             = to_none(cols[13])  # 비고
    cancel_date         = parse_date(cols[14])         # 취소일자
    transfer_apply_date = parse_date(cols[15])         # 양도양수적용일자
    transfer_end_date   = parse_date(cols[16])         # 양도양수종료일자
    serial_omit_yn      = to_none(cols[17]) or "N"     # 일련번호생략여부
    serial_omit_reason  = to_none(cols[18])            # 일련번호생략사유
    atc_code            = to_none(cols[19])            # ATC코드
    special_mgmt_type   = to_none(cols[20])            # 특수관리약품구분
    reader_device_type  = to_none(cols[21]) if len(cols) > 21 else None  # 의약품판독장비구분

    return (
        std_code, product_name, company_name, spec, total_qty,
        formulation_type, package_type, item_std_code, approval_date,
        med_category, rep_code, revised_code, generic_code, remarks,
        cancel_date, transfer_apply_date, transfer_end_date,
        serial_omit_yn, serial_omit_reason, atc_code,
        special_mgmt_type, reader_device_type,
    )

# ==========================================
# 6. 메인 로직
# ==========================================
def run(file_path: Path, encoding: str = "euc-kr"):
    if not file_path.exists():
        logger.critical(f"파일을 찾을 수 없습니다: {file_path}")
        raise SystemExit(1)

    connection = get_connection()
    total_inserted = 0
    total_skipped  = 0
    batch: list[tuple] = []

    logger.info(f"📂 파일 로딩 시작: {file_path}")

    try:
        with (
            file_path.open(encoding=encoding) as f,
            connection.cursor() as cursor,
        ):
            # 헤더 스킵
            header = f.readline()
            logger.info(f"헤더 확인: {header.strip()[:60]}...")

            for line_no, line in enumerate(f, start=2):
                line = line.rstrip("\r\n")
                if not line:
                    continue

                cols = line.split("|")
                if len(cols) < 21:
                    logger.warning(f"[{line_no}번째 줄] 컬럼 수 부족 ({len(cols)}개), 건너뜁니다.")
                    total_skipped += 1
                    continue

                try:
                    batch.append(parse_row(cols))
                except Exception as e:
                    logger.warning(f"[{line_no}번째 줄] 파싱 실패: {e}, 건너뜁니다.")
                    total_skipped += 1
                    continue

                # BATCH_SIZE마다 DB 저장
                if len(batch) >= BATCH_SIZE:
                    cursor.executemany(INSERT_SQL, batch)
                    connection.commit()
                    total_inserted += len(batch)
                    logger.info(f"  {total_inserted:,}건 저장 완료...")
                    batch.clear()

            # 나머지 잔여 데이터 저장
            if batch:
                cursor.executemany(INSERT_SQL, batch)
                connection.commit()
                total_inserted += len(batch)

        logger.info(f"✅ 완료! 총 {total_inserted:,}건 저장, {total_skipped:,}건 건너뜀.")

    except KeyboardInterrupt:
        logger.warning("사용자에 의해 강제 종료되었습니다.")
    except Exception as e:
        logger.exception(f"치명적인 오류: {e}")
    finally:
        connection.close()
        logger.info("DB 연결을 안전하게 종료했습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="의약품 바코드 마스터 데이터 적재 스크립트")
    parser.add_argument(
        "file",
        type=Path,
        help="적재할 파이프 구분자(|) 텍스트 파일 경로 (예: data/1_raw/BarCodeData.txt)",
    )
    parser.add_argument(
        "--encoding",
        default="euc-kr",
        help="파일 인코딩 (기본값: euc-kr, UTF-8 파일이면 utf-8-sig 입력)",
    )
    args = parser.parse_args()
    run(args.file, args.encoding)
