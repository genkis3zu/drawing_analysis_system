# Git Bash環境変数設定の調査結果

## 問題の概要
cygpathエラーが発生しており、`CLAUDE_CODE_GIT_BASH_PATH`環境変数が正しく設定されていない可能性があります。

```
Error: Command failed: cygpath -u 'C:\Users\mizuy\AppData\Local\Temp'
/usr/bin/bash: line 1: cygpath: command not found
```

## 一般的なGit Bashのインストールパス

以下のパスを確認しましたが、いずれもGit Bashがインストールされていませんでした：

1. `C:\Program Files\Git\bin\bash.exe` - 存在しない
2. `C:\Program Files (x86)\Git\bin\bash.exe` - 存在しない
3. `C:\Users\mizuy\AppData\Local\Programs\Git\bin\bash.exe` - 存在しない

## 推奨される解決方法

### 1. Git for Windowsのインストール確認

まず、Git for Windowsがインストールされているか確認してください：

```powershell
# PowerShellで実行
Get-Command git
```

### 2. Git Bashの実際のパスを特定

Git for Windowsがインストールされている場合：

```powershell
# PowerShellで実行
(Get-Command git).Source | Split-Path -Parent | Split-Path -Parent | Join-Path -ChildPath "bin\bash.exe"
```

### 3. 環境変数の設定

正しいパスが見つかったら、以下の方法で環境変数を設定します：

#### PowerShellで設定（管理者権限で実行）
```powershell
# ユーザー環境変数として設定
[Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", "C:\Program Files\Git\bin\bash.exe", "User")

# システム環境変数として設定（管理者権限必要）
[Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", "C:\Program Files\Git\bin\bash.exe", "Machine")
```

#### コントロールパネルから設定
1. Windowsキー + X → システム
2. システムの詳細設定 → 環境変数
3. ユーザー環境変数で「新規」をクリック
4. 変数名: `CLAUDE_CODE_GIT_BASH_PATH`
5. 変数値: Git Bashの実際のパス（例：`C:\Program Files\Git\bin\bash.exe`）

### 4. 設定の確認

設定後、新しいコマンドプロンプトまたはPowerShellを開いて確認：

```powershell
echo $env:CLAUDE_CODE_GIT_BASH_PATH
```

## 代替ソリューション

Git for WindowsではなくWSL（Windows Subsystem for Linux）を使用している場合は、WSLのbashを使用することも可能です：

```powershell
# WSLのbashパス
C:\Windows\System32\wsl.exe
```

## トラブルシューティング

1. **Git for Windowsが未インストールの場合**
   - https://git-scm.com/download/win からダウンロード
   - インストール時に「Git Bash」オプションを選択

2. **パスに空白が含まれる場合**
   - 環境変数の値を二重引用符で囲む必要はありません
   - 例：`C:\Program Files\Git\bin\bash.exe`（そのまま設定）

3. **Claude Codeの再起動**
   - 環境変数設定後、Claude Codeを再起動して変更を反映

## 参考情報

- Git for Windows公式サイト: https://gitforwindows.org/
- 環境変数の設定方法: https://docs.microsoft.com/ja-jp/windows/win32/procthread/environment-variables