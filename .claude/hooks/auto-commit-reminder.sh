#!/bin/bash
# 自動コミットリマインダー
# 重要な変更がある場合に強制的にコミットを促す

echo ""
echo "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
echo "         Git コミット リマインダー"
echo "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
echo ""

# 変更されたファイル数をカウント
MODIFIED_COUNT=$(git status --porcelain | wc -l)

if [ $MODIFIED_COUNT -gt 0 ]; then
    echo "[CRITICAL] $MODIFIED_COUNT 個のファイルが変更されています！"
    echo ""
    echo "変更されたファイル一覧："
    git status --short
    echo ""
    echo "📋 コミットチェックリスト："
    echo "□ 変更内容を確認しましたか？"
    echo "□ テストは通りましたか？"
    echo "□ コミットメッセージは準備できていますか？"
    echo ""
    echo "💾 今すぐコミットしてください："
    echo "   git add -A && git commit -m \"[変更内容の説明]\" && git push origin main"
    echo ""
    echo "⚠️  このリマインダーは変更がコミットされるまで表示され続けます"
else
    echo "[GOOD] すべての変更はコミット済みです ✅"
fi

echo ""
echo "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨"
echo ""