# Polygon API 调用参考

使用下列官方方法名。题目方法需要 `problemId`，比赛方法需要 `contestId`。遇到参数或接口变更时，核对 [Polygon API 文档](https://codeforces.github.io/polygon-misc/API.html)。

## 运行方式

令下列命令中的 `<skill目录>` 指向当前 SKILL.md 所在目录。使用 Python 3.9+，脚本仅导入标准库。命令的参数值不包含密钥。

```bash
python3 <skill目录>/scripts/polygon.py --init-env
python3 <skill目录>/scripts/polygon.py problems.list
python3 <skill目录>/scripts/polygon.py problem.info --param problemId=123456
python3 <skill目录>/scripts/polygon.py problem.saveStatement --param problemId=123456 --param lang=english --file-param legend=legend.tex
python3 <skill目录>/scripts/polygon.py problem.saveSolution --param problemId=123456 --param name=main.cpp --param tag=MA --param checkExisting=true --file-param file=main.cpp
python3 <skill目录>/scripts/polygon.py problem.commitChanges --param problemId=123456 --param minorChanges=true --param message=Update
python3 <skill目录>/scripts/polygon.py problem.buildPackage --param problemId=123456 --param full=true --param verify=true
python3 <skill目录>/scripts/polygon.py problem.package --param problemId=123456 --param packageId=987654 --param type=linux --output problem.zip
```

在 `.env` 中填写 `POLYGON_API_KEY` 和 `POLYGON_API_SECRET`。可选的 `POLYGON_PIN` 用作需要 PIN 的题目或比赛的默认值，可通过 `--param pin=...` 覆盖。脚本按自己的路径定位凭据，环境变量中的同名项优先。可用 `--env-file PATH` 选择另一个凭据文件。

用 `--params params.json` 传 UTF-8 JSON 参数对象，适合长题面或多个字段。JSON 数组用于同名重复参数，如 `{"testIndex":[1,2,3]}`。用 `--file-param 字段=文件路径` 读取 UTF-8 源码、题面、脚本或测试输入。对于要求 JSON 字符串的字段（如 `items`），在 params.json 中存为字符串。按官方文档提供每个方法的参数。

成功的 JSON 响应输出 `{"status":"OK","result":...}`，文本方法输出原文。用 `--output PATH` 保存完整 JSON、文本或 ZIP，避免大输出挤占上下文。下载题包必须指定输出文件。命令失败返回非零状态。客户端会拒绝自动跳转，报告网络、HTTP、Cloudflare 验证和 Polygon 业务错误。写请求结果含糊时查询状态后再重试。

## 方法与工作流

| 场景 | 官方方法 | 操作细节 |
|---|---|---|
| 连接与定位 | `problems.list`、`problem.create` | 先运行 `problems.list` 验证凭据。通过 id、name 或 owner 查找题目。创建使用 Polygon 内部题目标识，题面标题另设。 |
| 时空限制 | `problem.info`、`problem.updateInfo` | `timeLimit` 用毫秒，范围 250–15000，须为 50 的倍数。`memoryLimit` 用 MB。 |
| 题面与题解 | `problem.statements`、`problem.saveStatement`、`problem.renderStatements` | 指定 `lang`，只发送需修改的字段。标题需为单行。分别检查各语言的 HTML 和 PDF 渲染状态。 |
| 文件与角色 | `problem.files`、`problem.saveFile`、`problem.checker`、`problem.validator`、`problem.interactor`、`problem.setChecker`、`problem.setValidator`、`problem.setInteractor` | generator、validator、checker 和 interactor 以 `source` 类型上传文本源码。角色绑定使用已上传文件的准确文件名。 |
| 解答 | `problem.solutions`、`problem.saveSolution` | 主解设 `MA`，其他预期正确解设 `OK`，预期失败解按情况设 `WA`、`TL` 等。新增时传 `checkExisting=true`，编辑同名对象时按需传 `checkExisting=false`。 |
| 样例和测试 | `problem.tests`、`problem.saveTest`、`problem.testInput`、`problem.testAnswer`、`problem.previewTests` | `testset` 通常为 `tests`，先确认。样例设置 `testUseInStatements=true`。题面展示的输出字段不改变实际判题答案。生成预览可能异步完成。 |
| 生成脚本 | `problem.script`、`problem.saveScript` | 保存会替换整个脚本，编辑前读取原内容。 |
| 测试分组 | `problem.enableGroups`、`problem.enablePoints`、`problem.viewTestGroup`、`problem.saveTestGroup` | 新组通过为测试指定组名创建。组存在后再配置评分规则、反馈策略和依赖。 |
| 对拍 | `problem.stresses`、`problem.saveStress`、`problem.runStresses`、`problem.cancelStresses`、`problem.addStressCountertest` | 使用已上传的 generator 和待比较的解答。启动时指定对拍编号，轮询对应结果。仅在用户要求时将反例加入测试集。 |
| 修订和题包 | `problem.cautions`、`problem.commitChanges`、`problem.buildPackage`、`problem.packages` | 保存操作修改工作副本，提交才产生修订。区分 `committed=false` 的无变更和冲突。`verify=true` 启动验题。按包 ID 跟踪 `PENDING`、`RUNNING`、`READY` 或 `FAILED`。 |
| 验题和下载 | `problem.invocations`、`problem.invocation`、`problem.package` | 按包 ID 查找验题运行，查看解答名、测试点、判定、时间和内存。以题包状态和说明判断整体验题是否成功。题包 `READY` 后用 `problem.package` 和 `--output` 下载 ZIP，选择含生成测试的 Linux 包时传 `type=linux`。 |


## 其他读取与资源

用 `problem.viewFile` 配合 `type` 和 `name` 读取已有源码或资源，用 `problem.viewSolution` 和 `name` 读取已有解答。用 `problem.viewStatementResource`、`name` 及 `--output` 下载题面资源。上传命令的文件参数支持 UTF-8 文本。读取 `problem.script`、`problem.testInput` 和 `problem.testAnswer` 返回原始文本。

脚本也支持官方文档中的其他方法，包括 checker/validator 单元测试、issues、materials 和 contest.problems。删除、丢弃工作副本及修改访问权限时，按用户明确要求和文档参数执行。对拍启动后轮询 `problem.stresses`。构建启动后轮询 `problem.packages`，遇到终态即结束，避免反复启动任务。
