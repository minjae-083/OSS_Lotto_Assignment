# 6/45 Lotto Web

Django와 Docker로 구현한 6/45 로또 웹 사이트. 오픈소스SW기초 과제 결과물이다.

## 주요 기능

- 일반 사용자: 회원가입/로그인, 복권 구매(수동·자동), 당첨 확인
- 관리자: 회차별 판매 내역 조회, 추첨 실행, 당첨자 조회
- 동시 구매·추첨 시나리오에 대비한 트랜잭션 + 행 잠금 처리
- Docker 멀티컨테이너 구성 (web + db + nginx)

## 기술 스택

- Backend: Django 5.1, Python 3.12, Gunicorn
- Database: PostgreSQL 16
- Frontend: Django Templates + Bootstrap 5
- Infra: Docker, Docker Compose, nginx 1.27
- Test: pytest, pytest-django, pytest-cov

## 빠른 실행

```bash
git clone https://github.com/minjae-083/OSS_Lotto_Assignment.git
cd OSS_Lotto_Assignment
cp .env.example .env
docker compose up -d --build
```

빌드와 마이그레이션이 완료되면 <http://localhost/> 에서 홈 화면에 접근할 수 있다.
첫 부팅 시 `entrypoint.sh`가 마이그레이션과 정적 파일 수집을 자동으로 수행한다.

## 시연용 데이터 로드 (선택)

미리 구성된 1~5등 데모 데이터를 로드한다.

```bash
docker compose exec web python manage.py seed_demo
```

생성되는 계정은 다음과 같다.

| 계정 | 비밀번호 | 비고 |
|---|---|---|
| `admin` | `adminpass` | 슈퍼유저 |
| `alice` | `alicepass` | 1회차 1등 + 4등 당첨 |
| `bob` | `bobpass` | 1회차 2등 + 5등 당첨 |
| `carol` | `carolpass` | 1회차 3등 + 꽝 |

기존 데이터를 모두 삭제하고 다시 만들려면 `--reset` 옵션을 추가한다.

```bash
docker compose exec web python manage.py seed_demo --reset
```

## 테스트 실행

```bash
docker compose run --rm --entrypoint pytest web
```

26개의 테스트 케이스(서비스 단위 15건, 뷰/권한 10건, 통합 1건)가 실행되고
커버리지 요약이 함께 출력된다.

## 운영 명령

```bash
docker compose logs -f web   # 웹 컨테이너 로그 follow
docker compose down          # 컨테이너 정리 (DB 데이터는 볼륨에 유지)
docker compose down -v       # 볼륨까지 삭제 (DB 초기화)
```

## 디렉터리 구조

```
.
├── docker-compose.yml      # web + db + nginx 멀티컨테이너 정의
├── Dockerfile              # web 이미지 빌드 (Python 3.12-slim)
├── entrypoint.sh           # wait-for-db → migrate → collectstatic → gunicorn
├── nginx/default.conf      # 리버스 프록시 + 정적 파일 서빙
├── config/                 # Django 프로젝트 설정
├── accounts/               # 사용자 인증, 잔액 관리
├── lotto/                  # 회차/티켓 모델 + 비즈니스 로직(services.py)
├── admin_panel/            # 관리자 화면 (sales, draw, winners)
├── templates/base.html     # 공용 레이아웃
└── tests/                  # pytest 테스트
```

자세한 시스템 설계, 구현 과정, 테스트 결과는 별도 제출된 보고서 PDF에 포함되어 있다.
