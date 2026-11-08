## 宿題

### 取り組んだレベル
発展(a) ADK で作り直す。(b) の Pi も Codespaces で起動し、同じ質問を投げて比較した。

### やったこと
- `adk_agent/glossary_agent/` に `agent.py` と `__init__.py`（`from . import agent` の1行）を作成。`INSTRUCTIONS` は `app.agent` から、ツール（`search_glossary` / `get_lecture_summary` / 演習で作った `make_quiz`）は `app.tools` から import し、`app/` 配下は変更していない
- `PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent` で起動し、演習と同じ3つの質問を投げて Pydantic AI 版（`uv run python -m app.agent --trace "..."`）の結果と比較
- 初回起動時に ADK が `adk_agent/glossary_agent/.adk/session.db`（会話履歴の SQLite）を自動生成するため、`.adk/` を `.gitignore` に追加
- 副産物として、Pi を Codespaces に `npm install -g --ignore-scripts @earendil-works/pi-coding-agent` で導入し、`/model` で `gemini-3.8-flash` を選んで同じ3問を投げた

### 結果

#### 書き方の違い

| 観点 | Pydantic AI（演習 `app/agent.py`） | ADK（`adk_agent/glossary_agent/agent.py`） |
|---|---|---|
| エージェント定義 | `agent = Agent(instructions=INSTRUCTIONS)`。モデルは定義時には渡さない | `root_agent = Agent(model=..., name="glossary_agent", instruction=INSTRUCTIONS, tools=[...])`。`name` が必須で、モジュール変数名 `root_agent` が `adk run` の規約 |
| 指示の渡し方 | `instructions=`（複数形） | `instruction=`（単数形）。渡す文字列は同じ |
| ツールの渡し方 | 定義後に `agent.tool_plain(tools.search_glossary)` と1つずつ登録（`tool_plain` は RunContext を受け取らないツール用） | `tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz]` と関数のリストを一度に渡す。docstring と型ヒントからスキーマが自動生成される点は同じ |
| モデル指定 | 実行時に `agent.run_sync(question, model=GoogleModel(MODEL, provider=GoogleProvider(api_key=...)))`。モデル名は `app/config.py` が環境変数 `AIE_MODEL`（既定 `gemini-3.5-flash-lite`）から読む。定義と実行を分けているのは、テストで `TestModel` に差し替えるため | `model="gemini-3.5-flash-lite"` と素の文字列を定義時に固定。API キーは環境変数 `GEMINI_API_KEY` を ADK が自動で読む |
| 実行ループ・CLI | `main()` で argparse → `run_sync` → `print(result.output)` を自分で書いている（1問1プロセス） | `adk run <dir>` が対話 CLI ごと提供。自分で書くのは `root_agent` の定義だけ。複数ターンの会話が続く |
| トレース | `print_trace()` を自作し、`result.all_messages()` から `ToolCallPart` / `ToolReturnPart` を拾って `[tool call]` `[tool return]` `[usage]`（トークン数・コスト・requests・tool_calls）を表示 | CLI 上にはツール呼び出しもトークン数も表示されない。`/tmp/agents_log/agent.latest.log` にログが出る（`tail -F` で確認）。初回起動時にテレメトリ送信の可否を聞かれる |
| エラー処理 | `ModelHTTPError` を捕まえ、`api_error_message()` で 429/503 等を日本語メッセージに変換して終了。再試行はしない | 特に書いていない（ADK 側の既定動作） |
| 状態の永続化 | なし（プロセス終了で消える） | `.adk/session.db` に会話履歴を自動保存 |
| テスト | `TestModel` で API キーなしにツール呼び出しを検証できる（`uv run pytest -q`） | 今回は作っていない |
| 導入 | `pyproject.toml` に `pydantic-ai` が入っている | `uv run --with google-adk` で一時的に追加。`pyproject.toml` / `uv.lock` は変わらない。初回は取得に約1分 |

#### 回答の違い（同じ質問）

モデルはどちらも `gemini-3.5-flash-lite`（Pydantic AI 版は `config.py` の既定値、ADK 版は `agent.py` に直書き）。

##### 「RAG とは何ですか」

Pydantic AI 版（`--trace`）：
```
[model] gemini-3.5-flash-lite
申し訳ありません。ご質問の「RAG」について、講座の用語集を検索しましたが、用語集には登録されていないようです。

（関連する回：第2回）

--- trace ---
[tool call]   search_glossary({'query': 'RAG'})
[tool return] search_glossary -> [{"term": "ファインチューニング", "lecture": 2, "definition": "事前学習済みモデルを、…
[tool call]   search_glossary({'query': 'RAG'})
[tool return] search_glossary -> [{"term": "ファインチューニング", "lecture": 2, "definition": "事前学習済みモデルを、…
[usage] RunUsage(cost=Decimal('0.0006386'), input_tokens=1512, output_tokens=74, requests=3, tool_calls=2)
```

ADK 版：
```
用語集を検索しましたが、「RAG」に直接該当する用語や定義は登録されていませんでした。
（関連する仕組みとして、最新の事実などを覚えさせる手法としては「ツール」や「RAG」のような外部データを参照させるアプローチが挙げられています。）
```

比較：
- どちらも `search_glossary("RAG")` を呼び、「RAG」の項目はなく「ファインチューニング」の定義文（「最新の事実を覚えさせる用途には、ツールやRAGで外部データを参照させるほうが向く」）が定義文一致で返ってきている
- Pydantic AI 版は **同じ引数で search_glossary を2回呼んだ**（requests=3、tool_calls=2）。1回目の結果に「RAG」そのものがなかったので再検索したように見えるが、同じクエリなので無駄な呼び出し
- Pydantic AI 版はヒットした「ファインチューニング」の定義に触れず「登録されていない」とだけ答えた。ADK 版はその定義文の中の「ツールやRAGで外部データを参照する」を「関連する仕組み」として添えた。ツールの返り値は同じなのに、使い方が違う
- Pydantic AI 版は INSTRUCTIONS どおり末尾に「関連する回」を付けたが、ADK 版の RAG の回答には付いていない

##### 「第2回では何を学びますか」

Pydantic AI 版（`--trace`）：
```
[model] gemini-3.5-flash-lite
第2回では、「ファインチューニングとLoRA」をテーマに以下の内容を学びます。

- **事前学習とファインチューニングの違い**：ファインチューニングが向く場面や向かない場面の理解
- **SFT（教師ありファインチューニング）**：入力と望ましい出力のペアを使った学習の基本
- **PEFTとLoRA**：全パラメータを更新するのではなく、小さな低ランク行列だけを学習させてメモリやコストを大幅に抑える仕組み
- **QLoRAとの関係**：モデルを4bitに量子化してLoRAを組み合わせる方法（演習では小さなモデルをColab上でLoRA学習させ、学習前後の変化を確認します）

（第2回）

--- trace ---
[tool call]   get_lecture_summary({'lecture': 2})
[tool return] get_lecture_summary -> # 第2回 ファインチューニングとLoRA …
[usage] RunUsage(cost=Decimal('0.0008277'), input_tokens=1284, output_tokens=177, requests=2, tool_calls=1)
```

ADK 版：
```
第2回では、「ファインチューニングとLoRA」をテーマに以下の内容を学びます。

- 事前学習とファインチューニングの違い：ファインチューニングが向く場面（出力形式や口調の調整など）と向かない場面について理解します。
- SFT（教師あり微調整）：入力と出力のペアを用いた学習やデータの質の重要性を学びます。
- PEFTとLoRA：全パラメータを更新するのではなく、小さな低ランク行列のみを効率的に学習する手法（LoRA）の考え方を学びます。
- 演習：Google Colab上で小さなモデルをLoRAで学習させ、学習の前後でモデルの振る舞いがどう変わるかを体験します。
```

比較：どちらも `get_lecture_summary(2)` を1回呼び、返り値を4点に要約。書き出しの一文まで同じで、項目の切り方（QLoRA を独立させるか、演習を独立させるか）だけ違う。同じモデル・同じ指示・同じツールなら、フレームワークが違ってもほぼ同じ回答になる。

##### 「第3回のクイズを出して」

Pydantic AI 版（`--trace`）：
```
[model] gemini-3.5-flash-lite
第3回から確認問題を出します！

**【確認問題】**
Q. Pydantic AIに含まれる「TestModel」とはどのようなモデルで、どういった目的で使われるでしょうか？

---
第3回

--- trace ---
[tool call]   make_quiz({'lecture': 3})
[tool return] make_quiz -> {"question": "「TestModel」の意味は？", "answer": "Pydantic AIに含まれるテスト用の偽モデル。…
[usage] RunUsage(cost=Decimal('0.0004097'), input_tokens=849, output_tokens=62, requests=2, tool_calls=1)
```

ADK 版：
```
第3回の用語から確認問題です。

問題：
「ガードレール」の意味は何でしょうか？

答えのヒント：
エージェントが望ましくない行動や出力をしないように設ける制約や検査のことです。ルールを設定したり、ツールの権限を絞ったり、人の確認を挟むなどの方法があります。
```

比較：
- どちらも `make_quiz(3)` を1回呼んだ。用語はランダムに選ばれるので「TestModel」と「ガードレール」で異なる
- `make_quiz` は question と answer の両方を返すが、Pydantic AI 版は **答えを出さず問題だけ**を提示した。ADK 版は answer を「答えのヒント」としてほぼそのまま出している。INSTRUCTIONS の「宿題の答えそのものは書かず、考え方のヒントで導く」の解釈が割れた形で、Pydantic AI 版のほうが指示に忠実

#### おまけ：Pi との比較（発展 b）

Pi（gemini-3.8-flash）に同じ3問と、「app/tools.py を読んで、各ツールの役割を日本語で説明して」を投げた。Pi は用語集ツールを持たず、代わりに `read` / `bash` などの汎用ツールを持つ。

##### 同じ3問への Pi の挙動

| 質問 | Pi がやったこと | Pi の回答 |
|---|---|---|
| 「RAG とは何ですか」 | ツールを一切使わず回答 | 定義・必要性（ハルシネーション、カットオフ、社内データ）・3ステップ（検索→拡張→生成）・メリット・ユースケースを一般知識で長文回答 |
| 「第2回では何を学びますか」 | `ls -la` → `ls lectures/` → `read README.md` → `read data/lectures/02.md` → `read lectures/02/problem.md` と自分でリポジトリを探索。途中で Gemini API の 503（高負荷）が2回出たが自動で再試行して続行 | SFT・PEFT/LoRA・Colab 演習（Qwen3.5-0.8B、形式遵守率と内容正解率）・考察の4項目を詳細に回答 |
| 「第3回のクイズを出して」 | `ls lectures/03/` → `read data/lectures/03.md` → `read lectures/03/problem.md` を読んでから作問 | 空欄補充・正誤・選択式の3問を自作し、「回答が決まったら教えてください」と対話形式で返答 |

用語集エージェント（Pydantic AI 版・ADK 版）との違い：

- Pi は質問ごとに「調べるかどうか」を自分で判断する。RAG は調べず、講義回の質問ではファイルを探して読んだ。用語集エージェントは INSTRUCTIONS で「必ず用語集を確認する」と縛られているので、RAG でも必ず `search_glossary` を呼ぶ
- Pi は `get_lecture_summary(2)` が読むのと同じ `data/lectures/02.md` に自力でたどり着いたうえで、`problem.md` まで読んで答えている。結果として回答は詳しいが、ツールの返り値を超えて加筆している可能性がある。用語集エージェント2つの要約は短いがツールの返り値に忠実
- クイズは、用語集エージェントが `make_quiz` の仕様（用語1つ・問題と答え）に固定されるのに対し、Pi は形式も問数も自由に決めた
- Pi には API エラー時の自動再試行があるが、演習の `app/agent.py` は `ModelHTTPError` を日本語メッセージに変えて終了するだけで再試行しない

##### 「app/tools.py を読んで、各ツールの役割を日本語で説明して」

| | Pi（gemini-3.8-flash） | ADK 版用語集エージェント |
|---|---|---|
| 挙動 | `read app/tools.py:1-200` でファイルを実際に読んだ | 「ファイル自体を直接読み込むことはできない」と断ったうえで回答 |
| 回答内容 | 3ツールの役割に加え、search_glossary の照合順（完全一致→部分一致→定義文一致、最大3件）、`load_glossary` / `_normalize` / `_names` が内部補助関数であることまで説明 | 3ツールの役割をそれぞれ1〜2行で説明。内容は INSTRUCTIONS に書かれたツール説明の範囲で、実装の詳細には触れない。末尾に「関連回: 第1回 / 第2回」と用語集エージェントの出力形式が付いた |
| 回答の根拠 | ファイルの中身 | INSTRUCTIONS とツールのスキーマ（docstring） |

### 気づき・疑問
- 同じモデル・同じ INSTRUCTIONS・同じツール関数なら、Pydantic AI でも ADK git add lectures/03/answer.md
- ただし細部は違った。RAG の質問で Pydantic AI 版は同じ引数で `search_glossary` を2回呼んだ（無駄な API 呼び出し、requests=3）。ADK 版は検索結果の「ファインチューニング」の定義文から関連情報を拾ったが、Pydantic AI 版は捨てた。クイズでは Pydantic AI 版が答えを伏せ、ADK 版は答えを出した。同じ入力でも LLM の判断は揺れるので、1回の実行で「どちらが良い」とは言えない
- 用語集に「RAG」が未登録なのは意外だった（「ファインチューニング」の定義文の中にしか出てこない）。`search_glossary` が定義文の部分一致まで拾う設計だったから関連情報が返ったが、それを回答に活かすかはモデル次第。検索対象のデータとツールの検索ロジックが、そのままエージェントの回答の質の上限を決める
- Pi は用語集を使わず一般知識や自力のファイル探索で長文回答し、クイズも自作の3問形式になった。回答の「豊富さ」は Pi が上に見えるが、「用語集に基づいて答える」というエージェントの役割を守ったのは用語集エージェント側。何を正解とするかは、エージェントに何をさせたいかで決まる
- 同じ Gemini でも、持たせたツールで「答えられる範囲」が決まる。用語集エージェントはファイル読み取りツールを持たないので「読めない」と答えた一方、Pi は read ツールで中身を読んで実装の詳細まで説明できた
- Pydantic AI 版が「定義時にモデルを渡さず実行時に渡す」のは `TestModel` に差し替えてテストするためで、ADK 版のように定義に直書きすると同じ手が使いにくい。小さな違いだが、テストのしやすさに直結する設計判断だと分かった
- Pydantic AI 版の `--trace` は `[usage]` で1問あたりのコスト（約 $0.0004〜0.0008）・トークン数・requests・tool_calls まで出る。ADK 版はこれが CLI 上で見えないので、「ツールが2回呼ばれた」のような無駄に気づきにくい。学習用途では自作 trace のほうが分かりやすかった
- Pi はデフォルトで `gemini-3.1-pro` を使おうとして 429（無料枠の上限が 0）、次に選んだ `gemini-2.5-flash` は「新規ユーザーには提供終了」で 404、`gemini-3.8-flash` でようやく動いた。ツール側のモデル一覧と API 側の提供状況がずれている。講座の `config.py` が環境変数 `AIE_MODEL` でモデルを差し替えられるようにしているのは、こういう事態への備えとして合理的
- Pi は資料どおり確認なしでコマンドを実行する。回答後に誤って `source .venv/bin/activate` を貼ったところ、Pi はそれを指示と解釈して `which python`・`python3 -V` などを勝手に実行した。害のないコマンドだったが、実装レベルの `requires_approval=True` のような承認の仕組みがない怖さを実感した
- Pi はフッターに `↑11k ↓1.3k $0.013` と入出力トークン数・コストを常時表示する。第1回宿題で自分で計測し、第3回の `--trace` で `[usage]` として出しているものを、コーディングエージェントは UI に組み込んでいる
- 疑問：ADK 版はツール呼び出しの回数や引数を CLI 上で確認する標準的な方法があるのか（`adk web` の UI なら見える？）
- 疑問：Pydantic AI 版が同じ引数で `search_glossary` を2回呼んだのは、1回目の結果に「RAG」そのものがなかったから再検索したのか。docstring に「同じクエリを繰り返さない」と書けば防げるか（基礎レベルの実験として試す価値がありそう）