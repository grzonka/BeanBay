"""CLI entrypoint for BeanBay."""

import argparse


def main() -> None:
    """Start the BeanBay server."""
    import uvicorn

    parser = argparse.ArgumentParser(description="BeanBay")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()
    uvicorn.run("beanbay.main:app", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
