# GitHub 自动合并配置指南

## 当前状态

您的仓库已配置了自动合并 Pull Request 的功能，但目前没有开放的 Pull Request，所以还没有实际合并操作。

## 自动合并配置

已创建的工作流文件：`.github/workflows/auto-merge.yml`

### 配置说明

```yaml
name: Auto Merge Pull Requests

on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]
```

当以下事件发生时会触发自动合并：
- 打开新的 Pull Request
- 重新打开已关闭的 Pull Request
- Pull Request 准备好审查
- Pull Request 有新的提交

## 如何测试自动合并功能

### 方法1：创建测试 Pull Request

1. 创建一个新分支
2. 做一些修改
3. 创建 Pull Request
4. 观察 GitHub Actions 自动合并

### 方法2：使用命令行创建测试 PR

```bash
# 创建测试分支
git checkout -b test-branch

# 做一个简单的修改（例如修改 README）
echo "测试自动合并功能" >> README.md

# 提交并推送
git add .
git commit -m "Test auto merge"
git push origin test-branch

# 创建 Pull Request
gh pr create --title "测试自动合并" --body "测试自动合并功能"
```

## 手动合并 Pull Request

如果自动合并没有生效，可以手动合并：

### 方法1：使用 GitHub CLI

```bash
# 列出所有 Pull Requests
gh pr list

# 合并特定的 Pull Request
gh pr merge <PR编号> --merge

# 例如：合并第一个 PR
gh pr merge 1 --merge
```

### 方法2：使用 Git 命令

```bash
# 如果是自己的仓库，可以直接合并分支
git fetch origin
git checkout main  # 或 master
git merge origin/test-branch
git push origin main
```

### 方法3：使用 curl API

```bash
# 首先获取 PR 列表
curl -s -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/hummels-jp/AIAgent/pulls

# 然后合并特定的 PR（需要 Personal Access Token）
curl -X PUT -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/hummels-jp/AIAgent/pulls/<PR_NUMBER>/merge
```

## 常见问题

### Q: 为什么自动合并没有工作？

A: 可能的原因：
1. 没有开放的 Pull Request
2. GitHub Actions 权限不足
3. 分支保护规则阻止了自动合并
4. PR 有冲突

### Q: 如何检查 GitHub Actions 状态？

访问：https://github.com/hummels-jp/AIAgent/actions

### Q: 如何修改自动合并规则？

编辑 `.github/workflows/auto-merge.yml` 文件：
- `auto-merge-minimum-reviewers: 1` - 需要 1 个审查者
- `merge-method: squash` - 使用 squash 合并方式

## 当前仓库状态

- 主分支：master (54f7b5e)
- 另一个分支：main (fb81afc)
- 已配置：自动合并工作流

## 下一步

1. 确认需要合并哪个分支到哪个分支
2. 创建相应的 Pull Request
3. 观察自动合并是否生效
4. 如果需要，手动执行合并操作

## 获取帮助

- GitHub Actions 文档：https://docs.github.com/en/actions
- automerge-action 文档：https://github.com/pascalgn/automerge-action
