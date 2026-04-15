# /// script
# requires = ["requests", "pymysql", "python-dotenv"]
# ///

import os
import requests
import pymysql
import time
import math
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ==========================================
# 1. 환경 설정 및 초기화
# ==========================================
URL = os.getenv('UDI_API_URL')
DECODING_KEY = os.getenv('UDI_API_KEY')
NUM_OF_ROWS = 500  

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ==========================================
# 2. MariaDB 연결 정보
# ==========================================
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

print("MariaDB 연결 중...")
connection = pymysql.connect(
    host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
    charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
)

# ==========================================
# 3. 대용량 데이터 수집 및 적재 루프
# ==========================================
current_page = 1
total_inserted = 0

try:
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO mdv_udi_info (
                udidi_cd, prdlst_nm, clsf_grad_cd, prdt_nm_cont, biz_ipla_nm, 
                mdeq_prdlst_sn, udi_modl_nm_sn, care_sal_trgt_yn, 
                care_sal_cd_inpt_val, itgrt_info_reg_cmptn_dt
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                prdlst_nm = VALUES(prdlst_nm), clsf_grad_cd = VALUES(clsf_grad_cd),
                prdt_nm_cont = VALUES(prdt_nm_cont), biz_ipla_nm = VALUES(biz_ipla_nm),
                mdeq_prdlst_sn = VALUES(mdeq_prdlst_sn), udi_modl_nm_sn = VALUES(udi_modl_nm_sn),
                care_sal_trgt_yn = VALUES(care_sal_trgt_yn), care_sal_cd_inpt_val = VALUES(care_sal_cd_inpt_val),
                itgrt_info_reg_cmptn_dt = VALUES(itgrt_info_reg_cmptn_dt)
        """

        print("🚀 UDI 마스터 데이터 대량 수집을 시작합니다!")
        
        while True:
            params = {
                'serviceKey': DECODING_KEY,
                'pageNo': str(current_page),
                'numOfRows': str(NUM_OF_ROWS),
                'type': 'json'
            }

            try:
                response = requests.get(URL, params=params, headers=HEADERS, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"\n[에러] API 요청 실패 (페이지 {current_page}): {e}")
                print("10초 대기 후 해당 페이지를 재시도합니다...")
                time.sleep(10)
                continue

            body = data.get('body', {})
            items = body.get('items', [])
            total_count = body.get('totalCount', 0)

            if not items:
                print("\n✨ 더 이상 가져올 데이터가 없습니다. 수집 완료!")
                break

            insert_data = [
                (
                    item.get('UDIDI_CD'), item.get('PRDLST_NM'), item.get('CLSF_GRAD_CD'),
                    item.get('PRDT_NM_CONT'), item.get('BIZ_IPLA_NM'), item.get('MDEQ_PRDLST_SN'),
                    item.get('UDI_MODL_NM_SN'), item.get('CARE_SAL_TRGT_YN'),
                    item.get('CARE_SAL_CD_INPT_VAL'), item.get('ITGRT_INFO_REG_CMPTN_DT')
                ) for item in items
            ]

            cursor.executemany(sql, insert_data)
            connection.commit()
            
            total_inserted += len(items)
            total_pages = math.ceil(total_count / NUM_OF_ROWS)
            
            print(f"[{current_page}/{total_pages} 페이지] {len(items)}건 저장 완료 (누적: {total_inserted}/{total_count})")

            current_page += 1
            time.sleep(1.5) 

except KeyboardInterrupt:
    print("\n사용자에 의해 강제 종료되었습니다.")
except Exception as e:
    print(f"\n치명적인 시스템 에러: {e}")
finally:
    connection.close()
    print("DB 연결을 안전하게 종료했습니다.")