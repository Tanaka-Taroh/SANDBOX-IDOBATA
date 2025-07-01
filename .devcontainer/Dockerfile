# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# システムレベルの依存関係をインストール
# cron: 定期実行タスク用
# supervisor: プロセス管理用
# python3-pip: Pythonパッケージ管理用
# jq: JSON処理用
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    cron \
    supervisor \
    python3-pip \
    curl \
    jq \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# ログ、キャッシュ、設定用のディレクトリを作成し、非rootユーザー(vscode)に権限を付与
USER root
RUN mkdir -p /var/log/claude /var/cache/o3 /etc/supervisor/conf.d \
    && chown -R vscode:vscode /var/log/claude /var/cache/o3

# supervisorとcronの設定ファイルをコンテナにコピー
COPY .devcontainer/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY .devcontainer/claude-stats.cron /etc/cron.d/claude-stats

# cronジョブの権限設定と有効化
RUN chmod 0644 /etc/cron.d/claude-stats && crontab /etc/cron.d/claude-stats

# コンテナのメインプロセスとしてsupervisorを起動
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]