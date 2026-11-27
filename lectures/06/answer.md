# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：[tool call]   glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：
  [tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})
  [tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Using versioning in S3 buckets'})
- 気づき・疑問：
  - app/mcp_servers.json にサーバーを追記するだけで、エージェント側のコードを変えずにツールが 1 個 → 2 個 → 7 個と増えた。ローカルのコマンド起動（glossary、fetch）と URL 接続（aws）を同じ仕組みで扱える点が便利だと感じた。
  - 入力トークンが 715 → 2,230 → 11,153 と増えた。ツールの戻り値に加えて、ツール定義（特に aws の長い説明文）も毎回コンテキストを消費しているように見える。サーバーを増やすほどコストと精度に影響が出そうだが、必要なツールだけを見せる方法はあるのか。
  - STEP 4 では、日本語の検索語で的外れな結果（スキルの案内）が返ったあと、モデルが自分で英語の検索語に変えて再検索していた。
  - fetch のツール説明には「このツールでインターネットにアクセスできるようになった」とモデルに向けた指示が書かれている。ツール説明はサーバー提供者が書いたプロンプトとしてモデルに渡るので、信頼できないサーバーをつなぐとプロンプトインジェクションの経路になるのではないか。


## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：発展
- やったこと：Claude Code の公式 MCP ドキュメントを確認し、`app/mcp_servers.json` と比較した（確認日：2026-11-27）。
- 結果：
  - 設定場所：プロジェクトで共有する場合は、リポジトリのルートに `.mcp.json` を置く。`claude mcp add --scope project ...` でも登録できる。
  - コマンド起動：`claude mcp add --scope project --transport stdio glossary -- uv run python -m app.mcp_server` のように登録する。`--` より後ろがサーバー起動コマンドになる。JSONで書く場合は演習と同様に `command` と `args` を使う。
  - URL接続：`claude mcp add --scope project --transport http aws https://knowledge-mcp.global.api.aws` のように登録する。JSONでは `{"type": "http", "url": "https://knowledge-mcp.global.api.aws"}` のように `type` も指定する。演習の `app/mcp_servers.json` は `url` のみなので、この点が異なる。
  - 有効範囲：`project` は `.mcp.json` を通じてプロジェクトのメンバーと共有、`local`（既定）は自分の現在のプロジェクトだけ、`user` は自分のすべてのプロジェクトで有効。今回の例では `project` を指定した。
  - 公式ドキュメント（確認日：2026-11-27）：https://code.claude.com/docs/en/mcp
- 気づき・疑問：演習の設定形式とClaude CodeのJSON形式は似ているが、HTTPサーバーでは接続方式を表す `type` が必要。設定ファイル名や登録コマンド、共有範囲はソフトウェアごとに異なるため、他のクライアントの設定をそのまま流用できるとは限らない。
