"""検索・Graph取得のテスト（外部APIを呼ばない）。"""

import json

from app import retrieval


def test_graph_keeps_all_five_top_search_hits_as_seeds(tmp_path, monkeypatch):
    page_ids = [f"lec03-main-p{page:03}" for page in range(13, 18)]
    pages = [
        {
            "page_id": page_id,
            "document_id": "lec03-main",
            "lecture": 3,
            "document_title": "第3回",
            "section": "メモリ",
            "title": f"ページ{i}",
            "page": i,
            "content": f"本文{i}",
        }
        for i, page_id in enumerate(page_ids, start=1)
    ]
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")
    monkeypatch.setattr(retrieval, "RAG_GRAPH", graph_path)
    monkeypatch.setattr(retrieval, "load_pages", lambda _source: pages)
    monkeypatch.setattr(
        retrieval,
        "search",
        lambda _query: [
            {"page_id": page_id, "distance": i / 10}
            for i, page_id in enumerate(page_ids)
        ],
    )

    result = retrieval.search_graph("比較の質問")

    assert [page["page_id"] for page in result["seeds"]] == page_ids
    assert result["expanded"] == []
