"""
Streamlit의 공식 테스트 프레임워크(AppTest)로 app.py를 브라우저 없이 구동해
1) 6개 모델이 정상적으로 로딩되는지
2) 문서 업로드 -> 분류/OCR/요약/키워드/임베딩 파이프라인이 실제로 동작하는지
확인하는 스모크 테스트.
"""
import sys
import time
import traceback

from streamlit.testing.v1 import AppTest

print("=== [1/2] 앱 로드 및 모델 로딩 테스트 ===")
start = time.time()
at = AppTest.from_file("app.py", default_timeout=1800)
at.run()
print(f"앱 초기 실행 완료 ({time.time()-start:.1f}초)")

if at.exception:
    print("\n!!! 앱 실행 중 예외 발생 !!!")
    for e in at.exception:
        print(e)
    sys.exit(1)
else:
    print("예외 없음 - 모델 로딩 및 초기 렌더링 성공")

print("\n=== [2/2] 문서 처리 파이프라인 직접 호출 테스트 ===")
try:
    from app import load_models, process_document
    from PIL import Image
    import io

    models = load_models()
    print("load_models() 성공, 반환된 모델 개수:", len(models))

    test_images = ["receipt.jpg", "offical_document.jpg", "news.jpg"]
    for img_name in test_images:
        print(f"\n--- {img_name} 처리 중 ---")
        with open(img_name, "rb") as f:
            file_bytes = io.BytesIO(f.read())
        doc_type, content, summary, keywords, structured_data, img_data, embedding = process_document(file_bytes, models)
        print(f"[{img_name}] doc_type={doc_type}")
        print(f"[{img_name}] content(앞 80자)={content[:80]!r}")
        print(f"[{img_name}] summary={summary!r}")
        print(f"[{img_name}] keywords={keywords!r}")
        print(f"[{img_name}] structured_data={structured_data}")
        print(f"[{img_name}] embedding 길이={len(embedding) if embedding else 0}")

    print("\n=== 스모크 테스트 성공 ===")
except Exception:
    print("\n!!! 파이프라인 호출 중 예외 발생 !!!")
    traceback.print_exc()
    sys.exit(1)
