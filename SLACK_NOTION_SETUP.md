# 슬랙-노션 연동 설정 가이드

이 가이드는 슬랙 봇과 노션 연동을 위한 설정 방법을 안내합니다.

## 1. 슬랙 앱 설정

### 1.1 슬랙 앱 생성
1. [Slack API 포털](https://api.slack.com/apps)에 접속
2. "Create New App" → "From scratch" 선택
3. 앱 이름과 워크스페이스 선택

### 1.2 권한 설정
**OAuth & Permissions** 페이지에서 다음 권한 추가:

**Bot Token Scopes**:
- `app_mentions:read` - 봇 멘션 읽기
- `chat:write` - 메시지 전송
- `chat:write.public` - 공개 채널에서 메시지 전송
- `commands` - 슬래시 커맨드 사용
- `im:write` - DM(Direct Message) 전송 ⭐ 중요!
- `im:read` - DM 읽기
- `users:read` - 사용자 정보 읽기

⚠️ **DM 권한 중요사항**:
- `im:write` 권한이 없으면 `channel_not_found` 오류 발생
- 사용자가 먼저 봇과 대화를 시작해야 DM 전송 가능
- 권한 추가 후 반드시 **봇을 워크스페이스에 재설치** 필요

### 1.3 ngrok 설정 (로컬 개발용)
로컬에서 개발할 때는 슬랙이 접근할 수 있도록 ngrok을 먼저 설정해야 합니다:

```bash
# ngrok 설치 (macOS)
brew install ngrok

# 서버 실행 (별도 터미널)
make dev  # 또는 make docker-up

# ngrok으로 터널 생성 (새 터미널)
ngrok http 8000
```

ngrok 실행 후 나오는 **https URL**을 복사해두세요 (예: `https://abc123.ngrok.io`)

⚠️ **중요**: `127.0.0.1:8000` 같은 로컬 IP는 슬랙에서 접근할 수 없습니다!

### 1.4 슬래시 커맨드 생성
**Slash Commands** 페이지에서:
- Command: `/project`
- Request URL: `https://your-ngrok-url.ngrok.io/slack/commands`
- Description: "AI 프로젝트 관리 봇"

### 1.5 이벤트 구독 설정
**Event Subscriptions** 페이지에서:
- Request URL: `https://your-ngrok-url.ngrok.io/slack/events`
  - 입력 후 "Verified ✓" 표시가 나와야 합니다
  - 405 오류가 나오면 서버가 실행 중인지 확인하세요
- Subscribe to bot events:
  - `app_mention`
  - `message.channels` 
  - `message.im`

### 1.6 인터랙티브 컴포넌트 설정
**Interactivity & Shortcuts** 페이지에서:
- Request URL: `https://your-ngrok-url.ngrok.io/slack/interactive`

### 1.7 토큰 확인
- **Bot User OAuth Token**: `xoxb-`로 시작하는 토큰
- **Signing Secret**: App Credentials에서 확인

## 2. 노션 연동 설정

### 2.1 노션 Integration 생성
1. [Notion Integrations](https://www.notion.so/my-integrations)에 접속
2. "New Integration" 클릭
3. 이름 설정 후 "Submit" 클릭
4. **Internal Integration Token** 복사

### 2.2 노션 데이터베이스 준비
1. 노션에서 새 페이지 생성
2. 데이터베이스 생성 (`/table` 명령어 사용)
3. 다음 속성 추가:
   - Name (Title)
   - Status (Select: Planning, In Progress, Done)
   - Type (Select: Project, Epic, Story)
   - Created (Date)

### 2.3 Integration 권한 부여
1. 데이터베이스 페이지에서 "Share" 버튼 클릭
2. 생성한 Integration을 추가하고 "Edit" 권한 부여

### 2.4 데이터베이스 ID 확인
데이터베이스 URL에서 ID 추출:
```
https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                  이 부분이 DATABASE_ID
```

## 3. 환경 변수 설정

`.env` 파일에 다음 설정 추가:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Slack
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Notion
NOTION_TOKEN=secret_your-notion-integration-token
NOTION_DATABASE_ID=your-notion-database-id
```

## 4. 서버 실행

### 4.1 개발 환경
```bash
make install
make dev
```

### 4.2 프로덕션 환경
```bash
make install
make run
```

또는 Docker 사용:
```bash
make docker-build
```

## 5. 설정 확인 및 테스트

### 5.1 서버 실행 및 URL 확인
```bash
# 1. 서버 실행
make dev

# 2. 새 터미널에서 ngrok 실행
ngrok http 8000
```

### 5.2 슬랙 URL 검증
ngrok URL을 얻은 후:
1. 슬랙 앱 설정에서 각 URL 업데이트
2. "Event Subscriptions"에서 URL 입력 시 자동으로 검증됩니다
3. ✅ "Verified" 표시가 나오면 성공!

### 5.3 일반적인 오류 해결
- **405 Method Not Allowed**: 서버가 실행되지 않았거나 ngrok URL이 잘못됨
- **URL verification failed**: challenge 파라미터 처리 문제 (이제 해결됨)
- **Connection timeout**: ngrok이 실행되지 않았거나 포트가 다름

## 6. 사용 방법

### 6.1 슬랙에서 봇 사용
1. 슬랙 워크스페이스에서 `/project` 명령어 입력
2. "📝 에픽/스토리 생성" 버튼 클릭
3. 프로젝트 요구사항 입력
4. AI 분석 결과 확인
5. "✅ 승인 후 노션에 저장" 버튼으로 노션에 저장

### 6.2 주요 기능
- **AI 분석**: 자연어 요구사항을 에픽/스토리/포인트로 자동 변환
- **대화형 UI**: 슬랙 블록을 통한 직관적인 상호작용
- **단계별 확인**: 에픽 → 스토리 → 포인트 순서로 결과 검토
- **노션 자동 저장**: 승인 후 구조화된 프로젝트 페이지 생성

## 7. 문제 해결

### 7.1 슬랙 연결 문제

#### 405 Method Not Allowed 오류
```
INFO: 192.168.65.1:51468 - "GET /slack/events HTTP/1.1" 405 Method Not Allowed
```
**해결 방법**:
- ✅ 이제 GET 메서드가 지원됩니다
- 서버를 재시작하고 다시 시도하세요: `make dev`

#### URL 검증 실패
- ngrok이 실행 중인지 확인: `ngrok http 8000`
- 올바른 ngrok URL을 사용하고 있는지 확인 (https://)
- 서버가 8000번 포트에서 실행 중인지 확인

#### channel_not_found 오류 (DM 권한 문제)
```
SlackApiError: The request to the Slack API failed. 
The server responded with: {'ok': False, 'error': 'channel_not_found'}
```
**해결 방법**:
1. **권한 확인**: `im:write` 권한이 추가되어 있는지 확인
2. **봇 재설치**: 권한 추가 후 워크스페이스에 봇을 재설치
3. **대화 시작**: 사용자가 먼저 봇에게 DM을 보내거나 `/project` 명령어 실행
4. **대안**: 공개 채널에서 `/project` 명령어 사용

#### 토큰/시크릿 문제
- `.env` 파일에 올바른 토큰이 설정되어 있는지 확인:
  ```bash
  SLACK_BOT_TOKEN=xoxb-your-token-here
  SLACK_SIGNING_SECRET=your-secret-here
  ```

### 7.2 노션 연결 문제
- Integration Token이 `secret_`로 시작하는지 확인
- 데이터베이스 ID가 32자리 문자열인지 확인
- Integration에 데이터베이스 접근 권한이 있는지 확인

### 7.3 Import 오류 문제
#### cannot import name 'get_notion_service' from 'notion_client.client'
**해결됨**: 모듈명 충돌 문제가 해결되었습니다
- `src/notion_client/` → `src/notion_service/`로 변경됨
- 패키지 import 경로가 수정됨

### 7.4 로그 확인 및 디버깅
```bash
# 도커 로그 확인
make docker-logs

# 로컬 실행시 상세 로그
make dev-debug

# 슬랙 요청 로그 확인
# 서버 콘솔에서 다음과 같은 로그를 확인할 수 있습니다:
# INFO: Slack URL verification requested with challenge: xxx
# INFO: Slack event received
# INFO: Slack command received
```

### 7.5 단계별 테스트
1. **서버 접근 테스트**: `curl http://localhost:8000/health`
2. **ngrok 연결 테스트**: `curl https://your-ngrok-url.ngrok.io/health`
3. **슬랙 엔드포인트 테스트**: `curl https://your-ngrok-url.ngrok.io/slack/events`
4. **슬랙 앱에서 직접 테스트**: 워크스페이스에서 `/project` 명령어 실행

## 8. 다음 단계

기본 기능이 동작하면 다음과 같은 개선사항을 고려해보세요:

- **데이터베이스 연동**: 사용자 세션을 Redis나 PostgreSQL에 저장
- **사용자 권한**: 워크스페이스별 권한 관리
- **템플릿 기능**: 자주 사용하는 프로젝트 유형에 대한 템플릿
- **피드백 시스템**: AI 분석 결과에 대한 사용자 피드백 수집
- **통계 대시보드**: 프로젝트 진행 상황 시각화