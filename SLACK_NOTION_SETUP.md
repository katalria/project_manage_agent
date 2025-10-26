# 슬랙-노션 연동 설정 가이드

이 가이드는 슬랙 봇과 노션 연동을 위한 설정 방법을 안내합니다.

## 1. 슬랙 앱 설정

### 1.1 슬랙 앱 생성
1. [Slack API 포털](https://api.slack.com/apps)에 접속
2. "Create New App" → "From scratch" 선택
3. 앱 이름과 워크스페이스 선택

### 1.2 권한 설정
**OAuth & Permissions** 페이지에서 다음 권한 추가:
- `app_mentions:read`
- `chat:write` 
- `chat:write.public`
- `commands`
- `im:write`
- `users:read`

### 1.3 슬래시 커맨드 생성
**Slash Commands** 페이지에서:
- Command: `/project`
- Request URL: `https://your-domain.com/slack/commands`
- Description: "AI 프로젝트 관리 봇"

### 1.4 이벤트 구독 설정
**Event Subscriptions** 페이지에서:
- Request URL: `https://your-domain.com/slack/events`
- Subscribe to bot events:
  - `app_mention`
  - `message.channels`
  - `message.im`

### 1.5 인터랙티브 컴포넌트 설정
**Interactivity & Shortcuts** 페이지에서:
- Request URL: `https://your-domain.com/slack/interactive`

### 1.6 토큰 확인
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

## 5. ngrok을 이용한 로컬 테스트

로컬 개발시 슬랙이 접근할 수 있도록 ngrok 사용:

```bash
# ngrok 설치 (macOS)
brew install ngrok

# 터널 생성
ngrok http 8000

# ngrok에서 제공하는 https URL을 슬랙 설정에 사용
# 예: https://abc123.ngrok.io/slack/events
```

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
- 토큰과 시크릿이 올바른지 확인
- Request URL이 정확하게 설정되어 있는지 확인
- 서버가 실행 중이고 포트가 열려있는지 확인

### 7.2 노션 연결 문제
- Integration Token이 올바른지 확인
- 데이터베이스 ID가 정확한지 확인
- Integration에 데이터베이스 접근 권한이 있는지 확인

### 7.3 로그 확인
```bash
# 서버 로그 확인
make docker-logs

# 또는 로컬 실행시 콘솔에서 로그 확인
```

## 8. 다음 단계

기본 기능이 동작하면 다음과 같은 개선사항을 고려해보세요:

- **데이터베이스 연동**: 사용자 세션을 Redis나 PostgreSQL에 저장
- **사용자 권한**: 워크스페이스별 권한 관리
- **템플릿 기능**: 자주 사용하는 프로젝트 유형에 대한 템플릿
- **피드백 시스템**: AI 분석 결과에 대한 사용자 피드백 수집
- **통계 대시보드**: 프로젝트 진행 상황 시각화