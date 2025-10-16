#!/bin/bash

echo "========================================"
echo "📤 推送到 GitHub"
echo "========================================"
echo ""

# 检查是否是 Git 仓库
if [ ! -d ".git" ]; then
    echo "⚠️  这不是一个 Git 仓库，正在初始化..."
    git init
    echo "✅ Git 仓库初始化完成"
    echo ""
fi

# 查看状态
echo "📊 查看文件状态..."
git status
echo ""

# 添加所有文件
echo "📦 添加所有文件..."
git add .
echo "✅ 文件添加完成"
echo ""

# 提交
echo "💬 请输入提交信息（按回车使用默认）:"
read -p "提交信息: " commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="feat: v2.0 完整重构优化 - 实现核心限速功能"
fi

echo ""
echo "📝 提交更改..."
git commit -m "$commit_msg"
echo ""

# 检查远程仓库
if ! git remote -v > /dev/null 2>&1; then
    echo "⚠️  未配置远程仓库"
    echo ""
    echo "请在 GitHub 创建仓库后，运行以下命令:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/qbit-smart-controller.git"
    echo "git branch -M main"
    echo "git push -u origin main"
    echo ""
    exit 1
fi

# 推送
echo "🚀 推送到远程仓库..."
if git push; then
    echo ""
    echo "✅ 推送成功！"
    echo ""
    echo "🎉 你的代码已经在 GitHub 上了！"
    echo ""
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的原因:"
    echo "1. 需要设置上游分支: git push -u origin main"
    echo "2. 认证失败，请检查 GitHub Token"
    echo "3. 网络问题"
    echo ""
    exit 1
fi

