# 附录 C 命令、源码入口与版本说明 {#reference}

## 常用命令放在哪个输入框

下面是本书基准中的常用入口，供回查。不要把整张表当成一次必须全部执行的操作。选定一项任务，先理解命令目的，再在对应环境中运行。

| 输入位置 | 命令 | 作用 |
|---|---|---|
| 系统终端 | `node --version` | 查看 Node.js 版本 |
| 系统终端 | `pi --version` | 查看安装的 Pi 版本 |
| 系统终端 | `pi --help` | 查看当前版本的命令行帮助 |
| 系统终端 | `pi` | 在当前目录启动交互会话 |
| 系统终端 | `pi --continue` | 继续当前目录最近的会话 |
| 系统终端 | `pi --resume` | 打开保存会话的选择器 |
| Pi 输入框 | `/login` | 设置模型服务的登录或密钥 |
| Pi 输入框 | `/model` | 选择模型 |
| Pi 输入框 | `/session` | 查看当前会话信息与用量 |
| Pi 输入框 | `/name` | 设置会话名称 |
| Pi 输入框 | `/tree` | 查看或切换当前会话的历史分支 |
| Pi 输入框 | `/fork` | 从较早用户消息创建新会话 |
| Pi 输入框 | `/clone` | 把当前活动分支复制为新会话 |
| Pi 输入框 | `/compact` | 手动整理较早上下文为摘要 |
| Pi 输入框 | `/reload` | 按当前实现重新加载资源与配置 |
| Pi 输入框 | `/hotkeys` | 查看交互快捷键 |

源码开发者还会用到 **Pi 源码仓库**根目录中的几个入口：`./pi-test.sh` 从源码启动，`npm run check` 做检查并可能写入格式变化，`./test.sh` 在隔离环境中运行测试。这些文件不在当前书籍网站仓库中。具体测试需遵循 Pi 的 `AGENTS.md`，不要把真实模型评测与普通检查混为一谈。

## 从哪个文件开始找问题

| 阅读问题 | 首个入口 |
|---|---|
| 程序如何启动和选择模式 | `packages/coding-agent/src/main.ts` |
| 会话怎样组装 | `packages/coding-agent/src/core/sdk.ts` |
| 输入如何处理，扩展何时介入 | `packages/coding-agent/src/core/agent-session.ts` |
| 历史如何形成树 | `packages/coding-agent/src/core/session-manager.ts` |
| 模型和工具为何反复调用 | `packages/agent/src/agent-loop.ts` |
| 多家模型怎样统一请求 | `packages/ai/src/models.ts` |
| 消息和流式事件有哪些字段 | `packages/ai/src/types.ts` |
| 终端界面有哪些组件 | `packages/tui/src/index.ts` |
| 独立持久化运行时如何使用 | `packages/durable/README.md` |
| 跨进程对象和状态是什么 | `packages/chord/README.md` |
| 远程执行环境如何连接 | `packages/env/README.md` |

## 资料与署名

本书以仓库提交 `16f5f0af4d85ca583d045ceb5ed6d646fcaf7761` 为快照。各章已有具体源码链接，以下是进一步阅读的总入口：

- [工程 README](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/README.md)
- [开发规则 AGENTS.md](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/AGENTS.md)
- [命令行文档](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/cli.md)
- [SDK 文档](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/sdk.md)
- [扩展文档](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/extensions.md)
- [项目官方网站](https://pi.dev/)

固定源码链接用于核对本书，网站用于寻找后续更新。二者的版本范围不同；如果实际界面与书中不一致，先核对安装版本，再看对应文档。

Pi 项目采用 MIT 许可证。原项目版权声明为 `Copyright (c) 2025 Mario Zechner`。原始代码与文档的权利归原作者，许可证全文见[仓库 LICENSE](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/LICENSE)。本书中文解释、教学例子和示意图为针对当前工程编写的学习内容；它们不表示项目作者对本书进行了审核或背书。

封面和图示随书嵌入，未嵌入需要在线加载的图片、远程字体或运行脚本。字号、行距和实际分页由你的 EPUB 阅读器决定。阅读到此，你已经有了继续查证和扩展知识所需的目录地图、概念词表和源码入口。
