# 第三章 给整个工程画一张地图 {#ch03}

## 3.1 先按职责认路

第一次打开 Pi 仓库，你会看到很多包、测试、脚本和文档。若从第一个文件逐个往后读，很容易在尚未知道目的时就被实现细节淹没。更有效的办法是先问：这个目录解决什么问题？谁会使用它？它依赖什么？

根目录的 `README.md` 解释工程定位和基本用法；`AGENTS.md` 记录开发规则；`package.json` 组织工作区与脚本；`scripts/` 放各种构建、检查、发布和维护工具。产品与库的主体集中在 `packages/` 下。测试通常跟随各包放置，因此同一功能的实现和测试可能隔着一个 `src` 与 `test` 目录。

一个简化的目录地图如下。它只保留读书时需要先认识的部分，并非仓库的全部文件：

```text
pi/
  README.md                工程总览
  AGENTS.md                开发约定
  package.json             工作区和命令脚本
  packages/
    coding-agent/          CLI、SDK、会话和扩展
    agent/                 模型与工具执行循环
    ai/                    统一模型接口
    tui/                   终端界面
    durable/               独立持久化运行时
    chord/                 对象、契约和状态同步
    mcp/                   外部工具协议客户端
    codemode/              工具脚本执行沙箱
    env/                   远程执行环境
    telemetry/             执行追踪与指标
    evals/                 行为效果评估
  scripts/                 工程维护脚本
  pi-test.sh               从源码启动 Pi
  test.sh                  隔离环境的测试入口
```

这里的“启动脚本”和“测试脚本”尤其容易混淆。`pi-test.sh` 虽然名字里有 `test`，主要用途却是从源码启动 Pi；`test.sh` 才是仓库提供的隔离测试入口。判断命令用途，应看脚本内容，不应仅凭名字猜测。

## 3.2 默认 CLI 的主干是怎样分层的

用户启动的命令来自 `coding-agent`。它处理命令行参数，选择交互界面、一次性输出、JSON 流或 RPC，并组织会话、资源和模型配置。它还把工具、项目上下文和扩展组织成一个可以运行的会话。

`agent` 负责更通用的执行过程。它接收输入，让模型生成回复；模型提出工具调用时，执行工具并记录结果；有必要时继续请求模型。这个包不需要知道终端上用了哪种边框，也不需要自己实现每家模型厂商的协议。

`ai` 把不同模型服务整理成统一接口。服务的模型目录、认证、请求格式和流式协议存在差异，上层不应为每家服务复制一套 Agent 循环。`ai` 处理这些差异，上层围绕统一的消息和事件工作。

`tui` 负责终端显示和输入。它处理多行编辑、Markdown、选择列表、终端宽度等问题。流式内容不断增加时，界面可以按变化更新，而不是每次粗暴重画所有内容。这个包的关注点是“怎样在终端上显示”，与“下一步应调用什么工具”分开。

![默认 CLI 的主要层次：会话、Agent、模型接口与工具。](assets/architecture.png)

图中的箭头表示主要调用关系。工具结果会返回 Agent，模型流也会返回上层。实际实现还包含事件订阅、错误处理和取消信号；先掌握主干，再逐步补充这些细节。

## 3.3 扩展能力和另一条运行时路线

`mcp` 提供 Model Context Protocol 客户端。可以先把 MCP 理解为一种接入外部工具的通用协议：工具可能运行在另一个进程，也可能位于网络服务中。该包处理连接、请求和协议；它不自动决定模型何时使用工具。

`codemode` 允许模型生成一段 JavaScript，在受限制的执行环境中组合调用注入的工具。例如先读取多份数据，在脚本里整理，只把摘要交回模型。这样可以减少进入模型上下文的中间内容。它提供的是脚本执行机制，脚本能操作什么仍取决于宿主注入的工具。

`durable` 走的是独立持久化运行时路线。它直接建立在 `ai` 和 Chord 之上，组织会话、任务和提交，使进程重启后能够恢复未完成工作。默认 CLI 的 `AgentSession` 与它有不同的实现路径。看见两个模块都提到“会话”时，不能因此认为 CLI 的每次运行都自动采用了 Durable 的任务恢复语义。

`chord` 提供类型化契约、对象引用、跨进程调用和 JSON 状态同步等基础能力。“契约”可以理解为参与各方共同遵守的接口约定。Durable 使用 Chord 的状态相关能力，但 Chord 的全部功能不一定都出现在默认 CLI 中。

`env` 面向 Durable 的执行环境，把文件和命令操作放到远端机器。它包含 TypeScript 客户端和 Rust 守护进程，通过 SSH 等连接工作。`telemetry` 提供追踪与指标约定，帮助观察执行；`evals` 则关注 Agent 是否完成了预期任务。前者帮助解释过程，后者测量行为效果。

## 3.4 学会区分“包、入口和运行方式”

一个包可以有多个公开入口，一个入口也可能服务多种运行方式。例如 `coding-agent` 既提供命令行产品，也提供 SDK；交互模式和 RPC 模式共享会话核心，但外部接收输入和显示结果的方式不同。

“依赖”表示某个包的实现或类型使用另一个包。“运行方式”表示你怎样启动并使用它。两者不要混为一谈。SDK 程序依赖了 `coding-agent`，不代表它会自动打开终端界面；安装了 `durable`，也不代表原来的 `pi` 命令自动切换到新的运行时。

当你有一个新需求，可以据此缩小阅读范围：

| 想解决的问题 | 先看哪里 |
|---|---|
| 修改输入框、终端展示 | `packages/tui` 与 `packages/coding-agent/src/modes/interactive` |
| 理解模型为何继续调用工具 | `packages/agent/src/agent-loop.ts` |
| 接入另一家模型服务 | `ai` 的 Provider 与 API 相关代码 |
| 保存、分叉或恢复 CLI 对话 | `coding-agent` 的会话管理 |
| 增加自己的工具或命令 | `coding-agent` 的扩展接口和示例 |
| 在进程重启后恢复任务 | `durable` |
| 让工具在另一台机器执行 | `env` 与 Durable 的执行环境接口 |

找到包以后，也不必立刻读完整个包。先看 README、`package.json`、公共入口，再跟进与你的问题有关的函数。第十四章会用一条实际调用链示范这种读法。

### 本章小结

默认 CLI 的主干是 `coding-agent → agent → ai`，终端显示由 `tui` 支撑，工具提供实际操作。MCP 和代码模式扩展工具使用方式。Durable 则是独立运行时，Chord 和 env 为状态与执行环境提供基础。按职责找目录，比按文件顺序阅读更容易建立理解。

### 练习与参考答案

**练习一：** 想给自己的应用加一次模型调用，需要先读终端编辑器吗？

**参考答案：** 通常不需要。先从 `ai` 的统一模型接口开始，终端编辑器属于另一项职责。

**练习二：** 为什么不能把“CLI 可以恢复对话”理解成“所有工具任务都能在崩溃后自动续跑”？

**参考答案：** 对话历史与任务检查点是不同状态，默认 CLI 和 Durable 采用不同运行路径。后者才专门定义持久化任务和恢复行为。

**练习三：** 如何确认一个包实际依赖哪些其他包？

**参考答案：** 查看它自己的 `package.json`，并结合源码导入核对。根 README 是总览，未必列出全部包和全部依赖。

### 本章源码依据

- [根工作区与脚本配置](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/package.json)
- [coding-agent 的依赖与公开入口](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/package.json)
- [agent 的依赖](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/agent/package.json)
- [Durable 的定位](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/durable/README.md)
- [远程执行环境说明](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/env/README.md)
