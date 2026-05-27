"""
Mining Daily Agent - Main Entry Point

Usage:
    python -m client.main "Generate Pilbara lithium daily report"
"""

import asyncio
import sys

from .graph import run_agent


async def main(query: str) -> None:
    """Run the Mining Daily Agent with the given query."""
    print(f"\n{'='*60}")
    print(f"  Mining Daily Agent")
    print(f"  Query: {query}")
    print(f"{'='*60}\n")

    print("[1/6] Parsing intent...")
    result = await run_agent(query)

    print("[2/6] Building plan...")
    print("[3/6] Checking permissions...")
    print("[4/6] Executing tools...")
    print("[5/6] Aggregating results...")
    print("[6/6] Generating report...")

    print(f"\n{'='*60}")
    print(f"  Report saved to: {result.get('report_path', 'N/A')}")
    print(f"{'='*60}\n")

    report = result.get("report", "")
    if report:
        print(report)

    errors = result.get("errors", [])
    if errors:
        print(f"\n[WARNINGS]")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Generate Pilbara lithium daily report"
    asyncio.run(main(query))
