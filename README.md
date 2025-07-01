# Claude Code Development Container

Claude Code用の開発コンテナ環境です。AI駆動開発のための最適化された環境を提供します。

## 特徴

- **AI運用5原則**に基づいた開発環境
- **TDD（テスト駆動開発）**をサポート
- **"3人寄れば文殊の知恵with-o3"開発原則**の実装
- Claude Code、GeminiCLI、OpenAIcodex、o3の統合環境

## 開発環境の起動

### VS Code Dev Containers

1. このリポジトリをクローン
2. VS Code で開く
3. コマンドパレット（Ctrl+Shift+P / Cmd+Shift+P）
4. `Dev Containers: Reopen in Container` を選択

### GitHub Codespaces

1. GitHubリポジトリページで「Code」→「Codespaces」→「Create codespace」

## 前提条件

- Docker Desktop
- VS Code + Dev Containers拡張機能
- または GitHub Codespaces アクセス

## 開発原則

このプロジェクトは以下の原則に従います：

1. **第1原則：** AIはTDD、"3人寄れば文殊の知恵with-o3"開発原則、を厳守する
2. **第2原則：** AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る
3. **第3原則：** AIはツールであり決定権は常にユーザーにある
4. **第4原則：** AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する
5. **第5原則：** AIは全てのチャットの冒頭にこの5原則を逐語的に必ず画面出力してから対応する

## 含まれるツール

- Claude Code CLI
- Node.js 開発環境
- Git
- 統計情報収集（cron）
- supervisord（バックグラウンドサービス管理）

## 使用方法

詳細な開発ガイドラインは `CLAUDE.md` を参照してください。

## ライセンス

MIT License