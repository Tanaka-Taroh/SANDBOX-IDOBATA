````markdown
# `/idobata-init` — Command Reference

井戸端会議を開始し、**実行者 (ClaudeCode)**・**助言者 (Gemini CLI / OpenAI Codex)**・**リサーチャ (o3-mcp)** の“三位一体”体制を招集して  
要件・設計・タスクの 3 段階承認プロセスをスタートさせるコアコマンドです。

---

## Synopsis

```bash
/idobata-init <feature-name> [--overview <path>] [--no-search]
````

| 引数 / オプション       | 型      | 既定値                 | 説明                      |
| ---------------- | ------ | ------------------- | ----------------------- |
| `<feature-name>` | string | —                   | 井戸端会議で扱う新機能・改善点の識別子     |
| `--overview`     | path   | `.spec/overview.md` | プロジェクト概要を別パスから読み込む場合に指定 |
| `--no-search`    | flag   | false               | o3 事前リサーチをスキップしたいときに付与  |

---

## Workflow

| ステップ          | 処理内容                                    | 生成・更新ファイル                              |
| ------------- | --------------------------------------- | -------------------------------------- |
| 1. 役割召集       | 三ロールを対話コンテキストへ追加                        | —                                      |
| 2. 概要読込       | `overview.md` をコンテキストへ注入                | `.spec/overview.md`                    |
| 3. 事前リサーチ     | o3-mcp で `<feature-name>` を検索し要約        | `.spec/steering/RESEARCH_<feature>.md` |
| 4. ステアリングドラフト | 機能背景・価値・制約を下書き生成                        | `.spec/steering/STEERING_<feature>.md` |
| 5. 次フェーズ案内    | `/spec-requirements <feature-name>` を促す | —                                      |

---

## 標準出力例

```text
🎉 井戸端会議を開始しました: <feature-name>

📄 概要            : .spec/overview.md (409 tokens)
🔍 o3 事前調査     : .spec/steering/RESEARCH_<feature>.md
📝 ステアリング草稿 : .spec/steering/STEERING_<feature>.md

次のステップ: /spec-requirements <feature-name> を実行して要件を生成してください。
```

---

## 使用例

```bash
# 新機能 "multi-user-auth" の井戸端会議を開始
/idobata-init multi-user-auth

# プロジェクト概要を別ファイルから読み込んで開始
/idobata-init multi-user-auth --overview docs/overview_auth.md
```

---

## 関連コマンド

| コマンド                 | 役割              |
| -------------------- | --------------- |
| `/spec-requirements` | 要件フェーズを生成・承認    |
| `/spec-design`       | 設計フェーズを生成・承認    |
| `/spec-tasks`        | タスクフェーズを生成・承認   |
| `/mentor-help`       | 実装中の助言者呼び出し     |
| `/idobata-search`    | 追加リサーチ (o3-mcp) |
| `/postmortem`        | 振り返りテンプレート生成    |

---

## ベストプラクティス

1. **`overview.md` を必ず最新化**
   井戸端会議は概要を前提に議論するため、着手前に内容を点検してください。
2. **同時進行を避ける**
   `/project:idobata-init` は 1 機能ごとに実行し、並列会議は行わない方が混乱を防げます。
3. **検索スキップは例外的に**
   `--no-search` は機密情報やオフライン環境など正当な理由がある場合のみ使用し、結果を手動で共有してください。

```
::contentReference[oaicite:0]{index=0}
```
