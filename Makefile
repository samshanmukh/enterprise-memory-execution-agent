.PHONY: run dashboard test demo install clean

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

dashboard:
	streamlit run dashboard/app.py

test:
	python -m pytest tests/ -v

demo:
	@echo "\n=== Health Check ==="
	@curl -s http://localhost:8000/health | python3 -m json.tool | head -30
	@echo "\n=== Running Workflow (dry_run=true) ==="
	@curl -s -X POST http://localhost:8000/run-research-workflow \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Research MCP frameworks for enterprise adoption and create an execution plan.", "dry_run": true}' \
		| python3 -c "import sys,json; d=json.load(sys.stdin); \
			print('Status:        ', d['status']); \
			print('Confidence:    ', d['critique']['confidence_score']); \
			print('Approved:      ', d['critique']['approved']); \
			print('Docs stored:   ', d['memory']['docs_stored']); \
			print('Notion:        ', d['execution_results']['notion']['success']); \
			print('Linear tasks:  ', len(d['execution_results']['linear'])); \
			print('GitHub:        ', d['execution_results']['github']['success']); \
			print('Slack:         ', d['execution_results']['slack']['success']); \
			print('Gmail:         ', d['execution_results']['gmail']['success']); \
			print('Total actions: ', d['trace_summary']['total_actions']); \
			print('Run ID:        ', d['run_id'][:16]+'...')"
	@echo "\n=== Memory Search ==="
	@curl -s "http://localhost:8000/memory/search?q=MCP+enterprise&mode=hybrid" \
		| python3 -c "import sys,json; d=json.load(sys.stdin); \
			print('Vector results:   ', len(d['vector_results'])); \
			print('Knowledge records:', len(d['knowledge_records']))"
	@echo "\n=== Run History ==="
	@curl -s "http://localhost:8000/runs?limit=3" \
		| python3 -c "import sys,json; runs=json.load(sys.stdin); \
			[print(f'  {r[\"id\"][:12]}... {r[\"status\"]:10} {r[\"prompt\"][:50]}') for r in runs]"

clean:
	rm -rf data/ logs/ __pycache__ app/**/__pycache__ tests/__pycache__ .pytest_cache
