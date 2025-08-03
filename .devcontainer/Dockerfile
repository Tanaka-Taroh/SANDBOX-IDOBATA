# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# デバッグ: ベースイメージの状態を確認
RUN echo "=== Checking base image ===" && \
    which bash || echo "bash not found in base image" && \
    ls -la /bin/bash || echo "/bin/bash does not exist"

# システムレベルの依存関係をインストール
# bash: シェルスクリプト用（明示的にインストール）
# cron: 定期実行タスク用
# supervisor: プロセス管理用
# python3-pip, python3-venv: Pythonパッケージ管理用
# jq: JSON処理用
# rsync: ファイル同期用
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    bash \
    cron \
    supervisor \
    python3-pip \
    python3-venv \
    curl \
    jq \
    rsync \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# bashが正しくインストールされたか確認
RUN echo "=== Verifying bash installation ===" && \
    which bash && \
    bash --version && \
    ls -la /bin/bash

# ログ、キャッシュ、設定用のディレクトリを作成し、非rootユーザー(vscode)に権限を付与
USER root
RUN mkdir -p /var/log/claude /var/cache/o3 /etc/supervisor/conf.d /var/log/serena-mcp \
    && chown -R vscode:vscode /var/log/claude /var/cache/o3 /var/log/serena-mcp

# Python仮想環境を作成してアクティベート
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Serena-MCP dependencies
# 仮想環境内にPythonパッケージをインストール
RUN /opt/venv/bin/pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    python-lsp-server[all]>=1.9.0 \
    pylsp-mypy>=0.6.8 \
    tiktoken>=0.5.2 \
    pydantic>=2.5.0 \
    httpx>=0.26.0 \
    cachetools>=5.3.2

# supervisorとcronの設定ファイルをコンテナにコピー
COPY .devcontainer/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY .devcontainer/claude-stats.cron /etc/cron.d/claude-stats

# cronジョブの権限設定と有効化
RUN chmod 0644 /etc/cron.d/claude-stats && crontab /etc/cron.d/claude-stats

# ワークスペース用のディレクトリを準備
RUN mkdir -p /workspaces

# SerenaMCPのソースコードをコピー
COPY .devcontainer/serena-mcp /opt/serena-mcp

# SerenaMCPをインストール
RUN cd /opt/serena-mcp && \
    /opt/venv/bin/pip install -e .

# vscodeユーザーが仮想環境にアクセスできるようにする
RUN chown -R vscode:vscode /opt/venv /opt/serena-mcp

# コンテナのメインプロセスとしてsupervisorを起動
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]