#!/bin/bash
# Claude Code task-complete hook
# タスク完了時に自動的にコミットを促す

echo "================================"
echo "[HOOK] タスク完了フック"
echo "================================"
echo ""
echo "[TASK] タスクが完了しました！"
echo ""

# 現在の変更を確認
CHANGES=$(git status --porcelain)

if [ -n "$CHANGES" ]; then
    echo "[WARNING] 未コミットの変更があります："
    echo ""
    git status --short
    echo ""
    echo "[REMINDER] 🚨 重要な変更はGitHubにプッシュしましょう 🚨"
    echo ""
    echo "[ACTION] 推奨されるアクション："
    echo "1. git add -A"
    echo "2. git commit -m \"タスク完了: [タスク内容の説明]\""
    echo "3. git push origin main"
    echo ""
    echo "[URGENT] このメッセージを見たら必ずコミット＆プッシュしてください！"
else
    echo "[OK] すべての変更はコミット済みです"
fi

echo ""
echo "================================"