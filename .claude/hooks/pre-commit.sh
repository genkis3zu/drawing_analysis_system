#!/bin/bash
# Claude Code pre-commit hook
# 開発作業の節目で自動的にコミットを促す

echo "================================"
echo "📝 コミットリマインダー"
echo "================================"
echo ""
echo "現在の変更内容を確認してください："
echo ""

# 変更されたファイルを表示
git status --short

echo ""
echo "重要な作業を完了しましたか？"
echo "以下のタイミングでコミットすることを推奨します："
echo "  - 新機能の実装完了時"
echo "  - バグ修正完了時"
echo "  - テストの追加・更新時"
echo "  - リファクタリング完了時"
echo ""
echo "コミットする場合は以下のコマンドを実行してください："
echo "  git add -A"
echo "  git commit -m \"適切なコミットメッセージ\""
echo "  git push origin main"
echo ""
echo "================================"