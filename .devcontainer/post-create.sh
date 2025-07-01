#!/bin/bash
# 4つの主要AI CLIをすべてインストールし、o3-search-mcpを自動設定するスクリプト
set -e

# --- バージョン管理 ---
O3_SEARCH_MCP_VERSION="${O3_SEARCH_MCP_VERSION:-1.0.0}"
O3_SEARCH_MCP_ENDPOINT="${O3_SEARCH_MCP_ENDPOINT:-http://localhost:8080}"

echo "=== DevContainer AI Tools Setup ==="
echo "Starting installation of AI CLI tools..."

# --- 1. Anthropic Claude Code ---
echo ">>> 1/4: Installing official Claude Code..."
npm install -g @anthropic-ai/claude-code
echo ">>> Claude Code installed."

# --- 2. OpenAI Codex CLI ---
echo ">>> 2/4: Installing OpenAI Codex CLI..."
npm install -g @openai/codex
echo ">>> OpenAI Codex CLI installed."

# --- 3. Google Gemini CLI ---
echo ">>> 3/4: Installing Google Gemini CLI..."
npm install -g @google/gemini-cli
echo ">>> Google Gemini CLI installed."

# --- 4. o3-search-mcp (新規追加) ---
echo ">>> 4/4: Installing o3-search-mcp v${O3_SEARCH_MCP_VERSION}..."

# バージョン固定でインストール
if ! command -v o3-search-mcp &> /dev/null; then
    echo "Installing o3-search-mcp@${O3_SEARCH_MCP_VERSION}..."
    npm install -g o3-search-mcp@"${O3_SEARCH_MCP_VERSION}"
    echo ">>> o3-search-mcp installed successfully."
else
    echo ">>> o3-search-mcp already installed, skipping..."
fi

# --- シェルの共通設定 ---
# npmのグローバルインストール先を設定
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# .bashrcに、設定がまだ書き込まれていなければ追記する
BASHRC_FILE=~/.bashrc
if ! grep -q "# --- AI CLI Environment Settings ---" "$BASHRC_FILE"; then
  echo ">>> Configuring .bashrc for AI tools..."
  # より安全なヒアドキュメント形式で.bashrcに設定を追記
  cat <<'EOF' >> "$BASHRC_FILE"

# --- AI CLI Environment Settings ---
# Add Node + NPM global paths
export NPM_CONFIG_PREFIX="$HOME/.npm-global"
export PATH="$NPM_CONFIG_PREFIX/bin:$PATH"

# .envファイルからAPIキーを一行ずつ安全に読み込み、exportする
ENV_FILE="/workspaces/claude-sandbox/.env"
if [ -f "$ENV_FILE" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # コメント行と空行を無視する
        if [[ "$line" =~ ^\s*# ]] || [[ -z "$line" ]]; then
            continue
        fi
        export "$line"
    done < "$ENV_FILE"
fi
EOF
fi

# ターミナル起動時に設定を読み込むための設定
# .bash_profileが存在しない場合のみ作成
if [ ! -f ~/.bash_profile ]; then
    echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' > ~/.bash_profile
fi

# --- o3-search-mcp MCPサーバー設定 ---
echo ">>> Configuring o3-search-mcp as Claude MCP server..."

# 環境変数の確認
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY is not set. o3-search-mcp will not function properly."
    echo "   Please ensure your .env file contains: OPENAI_API_KEY=your-api-key"
else
    echo "✅ OPENAI_API_KEY detected (first 10 chars: ${OPENAI_API_KEY:0:10}...)"
fi

# Claude MCPサーバーとして登録
echo ">>> Registering o3-search-mcp with Claude MCP..."

# 登録の冪等性を確保（既に登録済みの場合はスキップ）
if claude mcp list 2>/dev/null | grep -q "o3"; then
    echo ">>> o3-search-mcp is already registered with Claude MCP, skipping..."
else
    echo ">>> Adding o3-search-mcp to Claude MCP..."
    # MCPサーバーとして登録
    claude mcp add o3 -s user \
        -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
        -e SEARCH_CONTEXT_SIZE=medium \
        -e REASONING_EFFORT=medium \
        -- npx o3-search-mcp@"${O3_SEARCH_MCP_VERSION}" || {
        echo "⚠️  Failed to register o3-search-mcp with Claude MCP."
        echo "   This might be due to missing OPENAI_API_KEY or network issues."
        echo "   You can manually register later using:"
        echo "   claude mcp add o3 -s user -e OPENAI_API_KEY=your-key -- npx o3-search-mcp"
    }
fi

# --- 最終確認 ---
echo ""
echo "=== Installation Summary ==="
echo "✅ Claude Code CLI: $(claude --version 2>/dev/null || echo 'installed')"
echo "✅ OpenAI Codex CLI: $(codex --version 2>/dev/null || echo 'installed')"
echo "✅ Google Gemini CLI: $(gemini --version 2>/dev/null || echo 'installed')"
echo "✅ o3-search-mcp: v${O3_SEARCH_MCP_VERSION}"

# MCP登録状況の確認
echo ""
echo "=== Claude MCP Status ==="
if command -v claude &> /dev/null; then
    claude mcp list 2>/dev/null || echo "⚠️  Unable to check MCP status (claude may not be fully initialized)"
else
    echo "⚠️  Claude CLI not available for MCP status check"
fi

echo ""
echo "🎉 Post-create setup completed successfully!"
echo ""
echo "📝 Next Steps:"
echo "   1. Ensure your .env file contains required API keys"
echo "   2. Restart your terminal or run: source ~/.bashrc"
echo "   3. Test o3-search-mcp: Try a search query in Claude Code"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check MCP status: claude mcp list"
echo "   - View logs: tail -f ~/.claude/logs/mcp.log"
echo "   - Manual registration: claude mcp add o3 -s user -e OPENAI_API_KEY=your-key -- npx o3-search-mcp"
echo ""