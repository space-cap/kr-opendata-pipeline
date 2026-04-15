-- 002_create_medicine_master_table.sql
-- 목적: 
-- 작성일: 

CREATE TABLE `medicine_master` (
    `id`                    BIGINT AUTO_INCREMENT COMMENT '내부 고유 ID',
    `std_code`              VARCHAR(20) NOT NULL COMMENT '표준코드(GTIN) - 바코드스캔용',
    `product_name`          VARCHAR(3000) NOT NULL COMMENT '한글상품명',
    `company_name`          VARCHAR(3000) COMMENT '업체명',
    `spec`                  VARCHAR(3000) COMMENT '약품규격',
    `total_qty`             INT DEFAULT 0 COMMENT '제품총수량',
    `formulation_type`      VARCHAR(50) COMMENT '제형구분',
    `package_type`          VARCHAR(50) COMMENT '포장형태',
    `item_std_code`         VARCHAR(20) COMMENT '품목기준코드',
    `approval_date`         DATE COMMENT '품목허가일자',
    `med_category`          VARCHAR(20) COMMENT '전문/일반/한약재',
    `rep_code`              VARCHAR(20) COMMENT '대표코드',
    `revised_code`          VARCHAR(20) COMMENT '제품코드(개정후)',
    `generic_code`          VARCHAR(50) COMMENT '일반명코드(성분명코드)',
    `remarks`               VARCHAR(3000) COMMENT '비고',
    `cancel_date`           DATE COMMENT '취소일자',
    `transfer_apply_date`   DATE COMMENT '양도양수적용(공고)일자',
    `transfer_end_date`     DATE COMMENT '양도양수종료일자',
    `serial_omit_yn`        CHAR(1) DEFAULT 'N' COMMENT '일련번호생략여부(Y/N)',
    `serial_omit_reason`    VARCHAR(3000) COMMENT '일련번호생략사유',
    `atc_code`              VARCHAR(20) COMMENT 'ATC코드',
    `special_mgmt_type`     VARCHAR(100) COMMENT '특수관리약품구분',
    `reader_device_type`    VARCHAR(50) COMMENT '의약품판독장비구분',
    
    `created_at`            DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '최초 등록일시',
    `updated_at`            DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 수정일시',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_std_code` (`std_code`), 
    INDEX `idx_product_name` (`product_name`(50)),
    INDEX `idx_company_name` (`company_name`),
    INDEX `idx_item_std_code` (`item_std_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='의약품 마스터(기준) 테이블';