format:
	@echo "formatting code..."
	@yapf -i -r --style .style.yapf bsc tests
	@echo "formatted code!"