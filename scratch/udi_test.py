import os
import requests
import pymysql
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. 설정 및 초기화
# ==========================================
url = os.getenv('UDI_API_URL')
decoding_key = os.getenv('UDI_API_KEY')

# API 페이징 변수 설정
NUM_OF_ROWS = 5
PAGE_NO = 1

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

params = {
    'serviceKey': decoding_key,
    'pageNo': str(PAGE_NO),
    'numOfRows': str(NUM_OF_ROWS), # 변수 적용
    'type': 'json'
}

print(f"API 호출 중 (페이지: {PAGE_NO}, 요청 건수: {NUM_OF_ROWS}건)...")
response = requests.get(url, params=params, headers=headers)
response.raise_for_status()

data = response.json()
items = data.get('body', {}).get('items', [])

if not items:
    print("가져올 데이터가 없습니다.")
    exit()

print(f"가져온 데이터 수: {len(items)}개")

# ==========================================
# 2. MariaDB에 데이터 삽입하기
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
                prdlst_nm = VALUES(prdlst_nm),
                clsf_grad_cd = VALUES(clsf_grad_cd),
                prdt_nm_cont = VALUES(prdt_nm_cont),
                biz_ipla_nm = VALUES(biz_ipla_nm),
                mdeq_prdlst_sn = VALUES(mdeq_prdlst_sn),
                udi_modl_nm_sn = VALUES(udi_modl_nm_sn),
                care_sal_trgt_yn = VALUES(care_sal_trgt_yn),
                care_sal_cd_inpt_val = VALUES(care_sal_cd_inpt_val),
                itgrt_info_reg_cmptn_dt = VALUES(itgrt_info_reg_cmptn_dt)
        """
        
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
    print(f"MariaDB 데이터 {len(items)}건 삽입 완료!")

except Exception as e:
    print(f"DB 저장 중 에러 발생: {e}")
    connection.rollback()
finally:
    connection.close()