docker:
	docker build -t ogn-rf -f Dockerfile.ogn-rf .
	docker build -t ogn-decode -f Dockerfile.ogn-decode .
	docker build -t ogn-filter -f Dockerfile.ogn-filter .
