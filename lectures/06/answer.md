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

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
