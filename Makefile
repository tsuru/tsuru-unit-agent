clean:
	@find . -name "*.pyc" -delete

deps:
	@echo "Installing deps"
	@pip install -r test-requirements.txt

test: clean deps
	@echo "Running tests"
	@py.test -s .
	@flake8 .
