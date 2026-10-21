# 从零读懂 Pi：AI 编程助手的工程入门

面向零基础读者的中文入门书，依据 Pi 源码编写。

**[在线阅读](https://aias00.github.io/pi-beginner-book-zh/) · [下载 EPUB](https://aias00.github.io/pi-beginner-book-zh/downloads/pi-beginner.epub)**

网站提供分章阅读、手机目录、字号调节、深浅主题和继续上次阅读；关闭 JavaScript 仍可阅读和导航。

- 阅读文件：`pi-beginner.epub`，约 629 KiB，可用 Apple Books、Calibre 或其他 EPUB 阅读器打开。
- 网页预览：`pi-beginner.html`，图片和样式已内嵌，可直接用浏览器离线打开。
- 完整书稿：`book.md`。
- 分章书稿：`chapters/`，按文件名前的编号排序。
- 封面、图示与排版：`assets/`。
- 内容统计：`book-info.json`；格式和链接检查结果：`validation.json`。

全书含前言、16 章、3 个附录，约 3.9 万汉字，配有 3 幅正文示意图和 48 道章末练习及参考答案。初次接触编程可先读第一至第四章，再沿书中的阅读路线深入。

内容依次介绍基本概念、目录地图、第一次使用、输入和工具调用、Agent 循环、多模型接口、会话和压缩、扩展与技能、终端界面、MCP 和代码模式、持久化、远程执行、源码阅读、开发测试和学习路线。

代码快照：`16f5f0af4d85ca583d045ceb5ed6d646fcaf7761`。整理日期：2026-10-20。源码引用固定到该快照，实际安装版本请另外核对。书中的教学轨迹不代表已实际调用模型或远程服务。

本仓库只包含书稿与阅读网站。书中 `packages/*`、`npm install`、`./pi-test.sh` 等指向 **Pi 源码仓库**，不是在本仓库运行。获取源码的步骤见第十五章。

## 本地预览与制作

如果只想阅读，无需安装制作工具。本站使用 Python 3.10+ 与 Pandoc，无 npm 依赖。网站构建兼容 Pandoc 3.1+；本版 EPUB 使用 Pandoc 3.12.1 制作。

```bash
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8000 --directory site
```

打开 `http://localhost:8000/` 预览。`chapters/` 是内容来源，`book-meta.yaml` 保存书籍信息；脚本自动合并为 `book.md`，并生成分章网站到 `site/`。`site/` 是构建产物，不提交到 Git。

修改章节或书籍信息后，先同步制作电子书，再检查：

```bash
python3 scripts/build.py --epub
python3 scripts/check.py
```

构建器检查电子书与书稿是否一致，避免网页更新后下载版本仍是旧内容。重新生成 EPUB 后应再次运行 EPUBCheck；`validation.json` 只记录其对应 SHA-256 文件的检查结果，不代替新版本验证。

推送到 `main` 后，GitHub Actions 自动构建、检查并发布 GitHub Pages。管理员首次启用 Pages 时，构建来源应选择 GitHub Actions。

## 来源与署名

本书是 AI 辅助编写的非官方学习读物，不代表 Pi 维护者审核或背书。Pi 原项目的 MIT 许可及原版权声明保留在 [LICENSES/pi-MIT.txt](LICENSES/pi-MIT.txt)，具体说明见 [NOTICE.md](NOTICE.md)。原项目许可的适用对象与本书新增内容分别说明。
