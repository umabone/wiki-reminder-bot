# 📢 Discord Reminder Bot (GitHub Actions)

任意の時間にDiscordのWebhookへ通知を送る簡単なBotです

## 使い方

1. `DISCORD_WEBHOOK_URL` をSecretsに登録
2. 自分のリポジトリにクローン
3. ブルアカ期間限定イベント通知が届く

## 構成

- GitHub Actionsでスケジューリング
- PythonでWebhook通知

## Webhook URLの管理

- URLはリポジトリの Settings → Secrets and variables → Actions に
  `DISCORD_WEBHOOK_URL` として登録してください。通知とLambdaデプロイの両方で使用します。
- Terraformにはデプロイ時に `TF_VAR_WEBHOOK_URL` 環境変数で渡します。
  Secretが空の場合、デプロイはTerraform実行前に失敗します。
- URLをコード、コミット、Issue、ログに貼らないでください。
  `terraform.tfvars` などのローカル設定ファイルはGit管理対象外です。
- ローカルでTerraformを実行する場合も、安全な方法で環境変数
  `TF_VAR_WEBHOOK_URL` を設定してください。URLをシェル履歴に残さないでください。
- `sensitive = true` はTerraformの通常の表示を伏せる設定です。
  URLはstateや保存したplanに含まれるため、これらも公開・コミットせず、
  アクセス制限された場所で管理してください。

### 公開したWebhookの対応手順

1. Discordのサーバー設定 → 連携サービス → ウェブフックで、公開したWebhookを削除します。
   通知は新しいWebhookの設定が完了するまで停止します。
2. 新しいWebhookを作成し、GitHub Actionsの `DISCORD_WEBHOOK_URL` Secretを更新します。
3. 修正をmainへ反映し、Lambdaデプロイが成功したことを確認します。
   GitHub Actionsの通知ワークフローも手動実行し、新しいWebhookへの通知を確認します。
4. 古いWebhookの無効化と両方の経路の動作確認が完了してから、漏洩のIssueを閉じます。

ファイルを削除しても過去のGit履歴からURLは消えません。
履歴の削除だけでは失効の代わりにならないため、古いWebhookの削除を優先してください。
