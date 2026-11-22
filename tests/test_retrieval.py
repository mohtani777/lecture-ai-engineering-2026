import json

from app import retrieval


def _page(page_id: str, title: str) -> dict:
    return {
        "page_id": page_id,
        "document_id": "lec02-main",
        "lecture": 2,
        "document_title": "基盤モデルの仕組み",
        "section": "テスト",
        "title": title,
        "page": 1,
        "content": title,
    }


def test_search_graph_follows_one_related_term_hop(monkeypatch, tmp_path):
    pages = {
        "lec02-main-p001": _page("lec02-main-p001", "開始ページ"),
        "lec02-main-p002": _page("lec02-main-p002", "関連語経由ページ"),
        "lec02-main-p003": _page("lec02-main-p003", "隣接ページ"),
    }
    graph = {
        "nodes": [
            {"id": "lec02-main-p001", "kind": "page", "title": "開始ページ"},
            {"id": "lec02-main-p002", "kind": "page", "title": "関連語経由ページ"},
            {"id": "lec02-main-p003", "kind": "page", "title": "隣接ページ"},
            {"id": "term:fine-tuning", "kind": "term", "title": "fine-tuning"},
            {"id": "term:lora", "kind": "term", "title": "LoRA"},
        ],
        "edges": [
            {"source": "lec02-main-p001", "target": "term:fine-tuning", "relation": "mentions"},
            {"source": "term:fine-tuning", "target": "term:lora", "relation": "related_term"},
            {"source": "term:lora", "target": "lec02-main-p002", "relation": "mentions"},
            {"source": "lec02-main-p001", "target": "lec02-main-p003", "relation": "next_page"},
        ],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(retrieval, "RAG_GRAPH", graph_path)
    monkeypatch.setattr(retrieval, "load_pages", lambda *args, **kwargs: list(pages.values()))
    monkeypatch.setattr(
        retrieval,
        "search",
        lambda query: [{
            "page_id": "lec02-main-p001",
            "distance": 0.1,
        }],
    )

    result = retrieval.search_graph("fine-tuning")

    assert [seed["page_id"] for seed in result["seeds"]] == ["lec02-main-p001"]
    expanded = {page["page_id"]: page for page in result["expanded"]}
    assert "lec02-main-p002" in expanded
    assert "lec02-main-p003" in expanded
    assert expanded["lec02-main-p002"]["path"] == [
        {"id": "lec02-main-p001", "title": "開始ページ"},
        {"id": "term:fine-tuning", "title": "fine-tuning"},
        {"id": "term:lora", "title": "LoRA"},
        {"id": "lec02-main-p002", "title": "関連語経由ページ"},
    ]
    assert expanded["lec02-main-p002"]["hops"] == 3
    assert result["max_hops"] == 2
    assert result["max_related_term_hops"] == 1
