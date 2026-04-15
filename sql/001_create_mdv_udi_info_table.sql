-- 001_create_mdv_udi_info_table.sql
-- 목적: 공공데이터 기반 의료기기 표준코드(UDI) 마스터 정보 저장
-- 작성일: 2024-05-22

CREATE TABLE IF NOT EXISTS mdv_udi_info (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '내부 고유 ID',
    udidi_cd VARCHAR(50) UNIQUE COMMENT '의료기기 표준코드 (UDI-DI)',
    prdlst_nm VARCHAR(1000) COMMENT '품목명',
    clsf_grad_cd VARCHAR(10) COMMENT '의료기기 등급',
    prdt_nm_cont VARCHAR(1000) COMMENT '제품명',
    biz_ipla_nm VARCHAR(1000) COMMENT '제조/수입업체명',
    mdeq_prdlst_sn VARCHAR(255) COMMENT '의료기기 품목 일련번호',
    udi_modl_nm_sn VARCHAR(50) COMMENT '모델명 일련번호',
    care_sal_trgt_yn CHAR(1) COMMENT '요양급여 대상 여부',
    care_sal_cd_inpt_val VARCHAR(255) COMMENT '요양급여 코드',
    itgrt_info_reg_cmptn_dt DATE COMMENT '통합정보 등록 완료일',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '데이터 생성 일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '데이터 최종 수정 일시'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='의료기기 표준코드 마스터 정보';