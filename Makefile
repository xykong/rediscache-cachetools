
build:
	uv build

patch:
	uvx hatch version patch

minor:
	uvx hatch version minor

major:
	uvx hatch version major
