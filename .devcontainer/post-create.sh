#!/bin/bash
# 4つの主要AI CLIをすべてインストールし、o3-search-mcpを自動設定するスクリプト
set -e

# --- tmuxのインストールをここに追加 ---
# command -v tmuxでコマンドの存在を確認し、なければインストール
if ! command -v tmux &> /dev/null; then
    echo ">>> Installing tmux..."
    # パッケージリストを更新してからtmuxをインストール
    sudo apt-get update && sudo apt-get install -y tmux
fi
# ------------------------------------

# --- バージョン管理 ---
O3_SEARCH_MCP_VERSION="${O3_SEARCH_MCP_VERSION:-1.0.0}"
O3_SEARCH_MCP_ENDPOINT="${O3_SEARCH_MCP_ENDPOINT:-http://localhost:8080}"

# --- NVMの初期化（DevContainer featuresでインストール済み） ---
echo ">>> Initializing NVM..."
export NVM_DIR="/usr/local/share/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # NVMを読み込み
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # bash_completionを読み込み

# Node.jsの確認とアクティブ化
echo ">>> Activating Node.js..."
nvm use node
echo ">>> Node.js version: $(node --version)"
echo ">>> npm version: $(npm --version)"

# --- npm を最新バージョンに更新 ---
echo ">>> Updating npm to latest version..."
npm install -g npm@latest
echo ">>> npm updated to $(npm --version)"

# --- 競合する設定をクリーンアップ ---
echo ">>> Cleaning up conflicting npm configurations..."
# .npmrcから競合する設定を削除
if [ -f ~/.npmrc ]; then
    sed -i '/^prefix=/d' ~/.npmrc
fi

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
# .bashrcに、設定がまだ書き込まれていなければ追記する
BASHRC_FILE=~/.bashrc
if ! grep -q "# --- AI CLI Environment Settings ---" "$BASHRC_FILE"; then
  echo ">>> Configuring .bashrc for AI tools..."
  # より安全なヒアドキュメント形式で.bashrcに設定を追記
  cat <<'EOF' >> "$BASHRC_FILE"

# --- AI CLI Environment Settings ---
# NVMの初期化（DevContainer featuresでインストール済み）
export NVM_DIR="/usr/local/share/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # NVMを読み込み
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # bash_completionを読み込み

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
# .bash_profileから.bashrcを確実に読み込む（SSH再接続対応）
if [ -f ~/.bash_profile ]; then
    # 既存の.bash_profileに.bashrc読み込み設定があるか確認
    if ! grep -q "source.*\.bashrc\|\..*\.bashrc" ~/.bash_profile; then
        echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' >> ~/.bash_profile
    fi

else
    echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' > ~/.bash_profile
fi

# Ensure NPM global binaries are available in PATH for this session
export PATH="$HOME/.npm-global/bin:$PATH"

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

# --- Research Environment Setup ---
echo ">>> Setting up research environment packages..."

# Python packages for research
pip3 install fabric pytest

# Verify essential tools are available
command -v rsync >/dev/null 2>&1 || { echo "WARNING: rsync not found - install via apt"; }

# Create tools.json template for Claude Code CLI
TOOLS_JSON_PATH="/workspaces/claude-sandbox/tools.json"
if [ ! -f "$TOOLS_JSON_PATH" ]; then
    echo ">>> Creating tools.json template..."
    cat <<'TOOLS_EOF' > "$TOOLS_JSON_PATH"
[
  {
    "name": "deploy_to_omega",
    "command": "fab push",
    "description": "Git-push & trigger post-receive hook on Omega"
  },
  {
    "name": "watch_log",
    "command": "fab tail",
    "description": "Tail the running simulation log on Omega"
  },
  {
    "name": "check_status",
    "command": "fab status",
    "description": "Check simulation status and recent logs on Omega"
  },
  {
    "name": "backup_results",
    "command": "fab backup",
    "description": "Backup simulation results on Omega"
  }
]
TOOLS_EOF
    echo ">>> tools.json template created."
fi

# Create fabfile.py template
FABFILE_PATH="/workspaces/claude-sandbox/fabfile.py"
if [ ! -f "$FABFILE_PATH" ]; then
    echo ">>> Creating fabfile.py template..."
    cat <<'FAB_EOF' > "$FABFILE_PATH"
from fabric import task, Connection

OMEGA = "Omega"

@task
def push(c):
    """Deploy code to Omega"""
    c.local("git push omega main")

@task
def tail(c):
    """Watch simulation logs"""
    conn = Connection(OMEGA)
    conn.run("tail -f /opt/sim/worktree/run.log")

@task
def status(c):
    """Check simulation status"""
    conn = Connection(OMEGA)
    conn.run("ps aux | grep simulate.sh")
    conn.run("tail -20 /opt/sim/worktree/run.log")

@task
def backup(c):
    """Backup simulation results"""
    conn = Connection(OMEGA)
    conn.run("rsync -av /opt/sim/worktree/results/ /opt/sim/backup/$(date +%Y%m%d)/")
FAB_EOF
    echo ">>> fabfile.py template created."
fi

echo ">>> Research environment setup completed."

echo ""
echo "🎉 Post-create setup completed successfully!"
echo ""
