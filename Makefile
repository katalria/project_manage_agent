.PHONY: install add

help:
	@echo "사용 가능한 명령어:"
	@echo "  -------------------------- poetry 관련 --------------------"
	@echo "  make add PKG=<패키지명>    - 패치키 추가"
	@echo "  make add PKG=<패키지명> WITH=<그룹명>   - 특정 그룹에 패치키 추가"
	@echo "  make install         - 패키지 설치"
	@echo "  make install WITH=<그룹명>   - 특정 그룹에 대한 패키지 설치. 예시: make install WITH=mac"
	@echo "  make update          - 패키지 업데이트"
	@echo "  make lint            - 코드 린트 체크 (flake8)"
	@echo "  make test            - 테스트 실행 (pytest)"
	@echo "  make shell           - Poetry 가상환경 내에서 셸 실행"
	@echo "  make jupyter         - jupyter notebook 서버 실행"
	@echo "  make run             - FastAPI 서버 실행"
	@echo "  make dev             - FastAPI 개발 서버 실행 (hot reload)"
	@echo "  make dev-debug       - FastAPI 개발 서버 실행 (debug mode)"
	@echo "  --------------------------- docker 관련 ----------------------"
	@echo "  make docker-up       - FastAPI docker container 실행"
	@echo "  make docker-build    - FastAPI docker container build 후 실행"
	@echo "  make docker-down     - docker container 종료"
	@echo "  make docker-in       - FastAPI docker container에 들어가기"
	@echo "  make docker-logs     - FastAPI container 로그 확인"
	@echo "  --------------------------- hydra 실험 관련 ----------------------"
	@echo "  run-exp <실험관련설정>     - 실험 진행하기. 예시: make run-exp logger=INFO"



add:
	@if [ -z "$(PKG)" ]; then \
		echo "Error: 패키지명을 지정하세요. 예: make add PKG=torch"; \
		exit 1; \
	fi
	poetry add $(PKG) $(if $(WITH), --group $(WITH),)

update:
	poetry update

install:
	poetry lock
	poetry install $(if $(WITH), --with $(WITH),)

lint:
	poetry run ruff check src

test:
	poetry run ruff check
	poetry run pytest

shell:
	poetry shell

jupyter:
	poetry run jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.disable_check_xsrf=True

run:
	poetry run python src/main.py

dev:
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-debug:
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

docker-up:
	docker compose up -d

docker-build:
	docker compose up -d --build

docker-down:
	docker compose down

docker-in:
	docker exec -it project_manage_agent-fastapi-1 bash

docker-logs:
	docker compose logs -f fastapi

run-exp:
	poetry run python src/train.py $(foreach v,$(filter-out $@,$(MAKECMDGOALS)), $(v)=$($(v)))

