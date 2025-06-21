#========================================
# Variables
#========================================
PYTHON       = python3
POETRY       = poetry
UVICORN      = uvicorn
ALEMBIC      = alembic
DOCKER_COMPOSE = docker-compose

#========================================
# Default target
#========================================
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make install         # تثبيت الاعتمادات (Poetry أو pip)"
	@echo "  make dev             # تشغيل الخادم في وضع التطوير"
	@echo "  make migrate         # تطبيق ترحيلات قاعدة البيانات"
	@echo "  make test            # تشغيل الاختبارات"
	@echo "  make lint            # فحص وتنسيق الكود"
	@echo "  make docs            # تشغيل وثائق API محلياً"
	@echo "  make docker-up       # بناء وتشغيل الحاويات"
	@echo "  make docker-down     # إيقاف الحاويات"
	@echo "  make clean           # تنظيف الملفات المؤقتة"

#========================================
# Install dependencies
#========================================
.PHONY: install
install:
	@echo "Installing dependencies..."
	$(POETRY) install

#========================================
# Development server
#========================================
.PHONY: dev
dev:
	@echo "Starting development server..."
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

#========================================
# Database migrations
#========================================
.PHONY: migrate
migrate:
	@echo "Running database migrations..."
	$(POETRY) run $(ALEMBIC) upgrade head

#========================================
# Testing
#========================================
.PHONY: test
test:
	@echo "Running test suite..."
	$(POETRY) run pytest --maxfail=1 --disable-warnings -q

#========================================
# Linting & Formatting
#========================================
.PHONY: lint
lint:
	@echo "Linting and formatting..."
	$(POETRY) run flake8 app
	$(POETRY) run black --check app
	$(POETRY) run isort --check-only app

#========================================
# API Documentation
#========================================
.PHONY: docs
docs:
	@echo "Opening API docs..."
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000 & \
	sleep 2 && xdg-open http://localhost:8000/docs

#========================================
# Docker Compose
#========================================
.PHONY: docker-up
docker-up:
	@echo "Building and starting Docker containers..."
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml up --build

.PHONY: docker-down
docker-down:
	@echo "Stopping Docker containers..."
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml down

#========================================
# Clean
#========================================
.PHONY: clean
clean:
	@echo "Removing __pycache__ and .pytest_cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
