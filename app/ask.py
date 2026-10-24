"""第1回: 会話履歴の有無を切り替えて素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --no-history "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    /exit                                # 対話を終了する

既定では同じチャットセッションで会話履歴を保つ。--no-history を指定すると、
質問ごとに独立して回答する。
講座に固有のことを聞くと、講座の実際とは違う答えをすることを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(client, question: str, chat=None) -> str:
    if chat is None:
        response = client.models.generate_content(model=MODEL, contents=question)
    else:
        response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 入力: 不明, 出力: 不明")
    else:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return response.text
    


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="質問ごとに独立して回答する（会話履歴を使わない）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    client = genai.Client(api_key=get_api_key())
    chat = None if args.no_history else client.chats.create(model=MODEL)

    try:
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(ask(client, question, chat))

            try:
                question = input("\n続けて質問できます（終了: /exit）> ").strip()
            except EOFError:
                print()
                break

            if question == "/exit":
                break
            if not question:
                continue
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
