import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.rag_service import rag_service


if __name__ == "__main__":
    print(asyncio.run(rag_service.build_vector_store(force=True)))

