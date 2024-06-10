docker:
	docker build -t ogn-configuration -f Dockerfile.ogn-configuration .
	docker build -t ogn-rf -f Dockerfile.ogn-rf .
	docker build -t ogn-decode -f Dockerfile.ogn-decode .
	docker build -t aprs-filter -f Dockerfile.aprs-filter .
