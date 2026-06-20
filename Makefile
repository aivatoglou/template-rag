.PHONY: install test up logs down

install:
	@echo "Installing dependencies..."
	uv sync

test:
	@echo "Running tests..."
	uv run pytest tests/ -v

up:
	@echo "Starting the application..."
	docker compose up --build -d 
	@echo ""
	@echo "Services started:"
	@echo "    API: 		http://localhost:8000"
	@echo "    Docs: 		http://localhost:8000/docs"
	@echo "    PostgreSQL: 	localhost:5432"

logs:
	@echo "Showing application logs..."
	docker compose logs -f

down:
	@echo "Stopping the application..."
	docker compose down -v