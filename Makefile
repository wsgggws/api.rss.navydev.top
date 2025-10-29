ARGS ?=

# 告诉 make 这三个名字不是文件名，而是“伪目标”（phony targets）。
.PHONY: install test local-run local-otel-run local-celery-start local-celery-stop docker-run docker-stop docker-cleanup

# @ 前缀：让这个命令在执行时不打印命令本身，只输出脚本中的 echo 和结果，保持输出干净。

install:
	@uv sync

test:
	@./scripts/make-test.sh $(ARGS)

local-run:
	@./scripts/local-run.sh

local-celery-start:
	@./scripts/local-celery-start.sh

local-celery-stop:
	@./scripts/local-celery-stop.sh

local-otel-run:
	@./scripts/local-otel-run.sh

docker-run:
	@./scripts/docker-run.sh

docker-stop:
	@./scripts/docker-stop.sh

docker-cleanup:
	@./scripts/docker-cleanup.sh
