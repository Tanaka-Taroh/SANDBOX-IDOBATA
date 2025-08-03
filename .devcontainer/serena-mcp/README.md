# Serena MCP - Semantic Code Intelligence for Claude

Serena MCP は、Language Server Protocol (LSP) を活用して、Claude に高度なコードインテリジェンス機能を提供する MCP サーバーです。

## 主な機能

- **シンボル検索**: プロジェクト全体から関数、クラス、変数を高速検索
- **コンテキスト抽出**: 最小限のトークンで最大限の情報を提供
- **セマンティック編集**: コード構造を理解した上での編集機能

## インストール

```bash
# Clone the repository
git clone https://github.com/your-org/serena-mcp.git
cd serena-mcp

# Install dependencies
pip install -r requirements.txt
```

## Claude での使用方法

### 1. Claude MCP への登録

```bash
claude mcp add serena -s user -- python -m serena_mcp --stdio
```

### 2. 動作確認

```bash
claude mcp list
```

## 開発モード

### FastAPI サーバーとして起動

```bash
python -m serena_mcp
```

ブラウザで http://localhost:24282 にアクセスして Web UI を確認できます。

### stdio モードでテスト

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python -m serena_mcp --stdio
```

## トラブルシューティング

### 接続に失敗する場合

1. Python パスを確認:
   ```bash
   which python
   ```

2. 作業ディレクトリを指定して再登録:
   ```bash
   claude mcp remove serena
   claude mcp add serena -s user -e PYTHONPATH=/path/to/serena-mcp/src -- python -m serena_mcp --stdio
   ```

### ログの確認

stderr にログが出力されます。詳細なログを見るには:

```bash
export SERENA_MCP_LOG_LEVEL=DEBUG
```

## ライセンス

MIT License