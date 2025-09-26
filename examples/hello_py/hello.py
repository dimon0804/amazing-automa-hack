def greet(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        print(greet(sys.argv[1]))
    else:
        print("Usage: python -m hello <name>")
