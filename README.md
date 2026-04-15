# 🇰🇷 KR OpenData Pipeline

국내 공공데이터포털(data.go.kr) 및 식약처에서 제공하는 의료기기 및 의약품 데이터를 MariaDB에 자동으로 수집하고 적재하는 데이터 파이프라인 프로젝트입니다.

---

## ✨ 핵심 기능

- **📦 의료기기 UDI 마스터 수집 (`collect_udi_master.py`)**
  - 식약처 API(`getMdvUdiInfo`)를 통한 대용량 데이터 동기화.
  - **체크포인트 기능:** 중단 시 마지막 수집 지점부터 자동으로 재개.
  - **Upsert 지원:** 동일 코드 데이터 발생 시 최신 정보로 업데이트.

- **💊 의약품 바코드 마스터 적재 (`load_medicine_master.py`)**
  - 대용량 파이프 구분(`|`) 텍스트 파일 배치 적재.
  - **데이터 정제:** 잘못된 날짜(예: 11월 31일) 자동 감지 및 보정.
  - **EUC-KR/CP949 지원:** 공공데이터 특유의 인코딩 문제 완벽 대응.

- **🛡️ 안정성 및 관리**
  - 모든 작업 로그를 `logs/` 폴더에 체계적으로 기록.
  - `.env`를 통한 환경 변수 관리 및 유효성 검사.
  - `uv`를 활용한 빠르고 격리된 파이썬 환경 관리.

---

## 🛠️ 기술 스택

- **Language:** Python 3.12+
- **Environment:** [uv](https://github.com/astral-sh/uv) (Python package & environment manager)
- **Database:** MariaDB / MySQL
- **Libraries:** `requests`, `pymysql`, `python-dotenv`

---

## 🚀 시작하기

### 1. 전제 조건
- [uv](https://docs.astral.sh/uv/)가 설치되어 있어야 합니다.
- MariaDB 또는 MySQL 서버가 가동 중이어야 합니다.

### 2. 설치 및 환경 설정
```bash
# 저장소 복제
git clone https://github.com/space-cap/kr-opendata-pipeline.git
cd kr-opendata-pipeline

# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 DB 접속 정보와 API 키를 입력하세요.
```

### 3. 데이터베이스 테이블 생성
`sql/` 폴더에 있는 스크립트를 순서대로 실행하여 테이블을 생성합니다.
1. `sql/001_create_mdv_udi_info_table.sql`
2. `sql/002_create_medicine_master_table.sql`

---

## 📖 사용 방법

### 의료기기 UDI 수집
전체 데이터를 API로부터 수집합니다. 중단 시 마지막 페이지부터 이어서 진행됩니다.
```powershell
uv run scripts/collect_udi_master.py

# 옵션: 특정 페이지부터 시작
uv run scripts/collect_udi_master.py --start-page 100
```

### 의약품 마스터 데이터 적재
배포된 텍스트 파일을 DB로 로드합니다.
```powershell
# EUC-KR 파일 적재 (기본)
uv run scripts/load_medicine_master.py data/1_raw/BarCodeData.txt

# UTF-8 파일 적재 시
uv run scripts/load_medicine_master.py data/1_raw/BarCodeData.txt --encoding utf-8-sig
```

---

## 📂 프로젝트 구조

```text
kr-opendata-pipeline/
├── data/               # 데이터 소스 파일
├── docs/               # 설계 및 명세 문서
├── logs/               # 실행 로그 파일 (.gitignore)
├── scripts/            # 데이터 수집/적재 파이썬 스크립트
├── sql/                # DB 테이블 생성 스크립트
├── .env.example        # 환경 변수 샘플
├── pyproject.toml      # uv 설정 및 의존성 관리
└── README.md
```

---

## ⚠️ 주의사항

> [!IMPORTANT]
> - **API 키 보안:** `UDI_API_KEY`가 포함된 `.env` 파일이 공유되지 않도록 주의하세요 (이미 `.gitignore`에 포함됨).
> - **인코딩 오류:** 한글이 깨질 경우 `--encoding` 옵션을 `cp949` 또는 `euc-kr`로 번갈아 시도해 보세요.
> - **DB 컬럼 길이:** 제품명이 매우 긴 경우 `Data too long` 에러가 발생할 수 있습니다. 이 경우 SQL 스크립트의 `VARCHAR` 길이를 조정하세요.

---

## 📄 라이선스
MIT License. 자유롭게 사용 및 수정 가능합니다.
