"""End-to-end verification for the document archive project.

Checks more than app startup:
- model loading
- document classification/OCR/summary/keywords/embedding
- SQLite persistence
- keyword search
- vector similarity search
"""

import io
import json
from pathlib import Path

from sqlmodel import Session, select

import app


SAMPLE_FILES = ["receipt.jpg", "offical_document.jpg", "news.jpg"]


def main():
  models = app.load_models()
  assert len(models) == 10
  embedding_model = models[9]

  saved_ids = []
  with Session(app.engine) as session:
    for filename in SAMPLE_FILES:
      path = Path(filename)
      assert path.exists(), f"missing sample file: {filename}"

      with path.open("rb") as f:
        uploaded = io.BytesIO(f.read())
      uploaded.name = filename

      doc_type, content, summary, keywords, structured_data, img_data, embedding = app.process_document(uploaded, models)

      assert doc_type
      assert content and len(content) > 10
      assert summary
      assert keywords
      assert isinstance(structured_data, dict)
      assert img_data
      assert embedding and len(embedding) > 100

      doc = app.Document(
        filename=f"full_check_{filename}",
        doc_type=doc_type,
        content=content,
        summary=summary,
        keywords=keywords,
        structured_data=json.dumps(structured_data, ensure_ascii=False),
        image_data=img_data,
        embedding=json.dumps(embedding),
      )
      session.add(doc)
      session.commit()
      session.refresh(doc)
      saved_ids.append(doc.id)
      print(f"processed and saved: {filename} -> id={doc.id}, type={doc_type}, embedding={len(embedding)}")

    keyword_results = session.exec(
      select(app.Document).where(app.Document.filename.contains("full_check_"))
    ).all()
    assert len(keyword_results) >= len(SAMPLE_FILES)
    print(f"keyword/db search ok: {len(keyword_results)} full_check docs")

    vector_results = app.search_by_similarity("영수증 금액 날짜", embedding_model, session)
    assert vector_results
    print(f"vector search ok: {len(vector_results)} results")

  print("document archive full check passed")


if __name__ == "__main__":
  main()
