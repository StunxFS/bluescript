format:
	@echo "formatting code..."
	@yapf -i -r --style .style.yapf bsc
	@echo "formatted code!"