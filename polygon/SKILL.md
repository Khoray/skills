---
name: polygon
description: 使用 Codeforces Polygon 编写、导入、编辑和验收算法竞赛题。适用于查找 Polygon 题目、准备 LaTeX 题面和题解、上传标程与 testlib checker、validator、generator 或 interactor、配置样例与测试组、对拍、提交修订、查看验题结果及下载题包。
---

# Polygon 出题

1. 确定用户要起草题目、检查现有题，还是写入 Polygon。通过本 skill 的 `scripts/polygon.py` 直接调用官方 API。运行环境需具备 Python 3.9+ 标准库和 Polygon 网络访问。首次使用时执行 `python3 <skill目录>/scripts/polygon.py --init-env`，在 skill 根目录生成 `.env`，让用户填写 `POLYGON_API_KEY` 和 `POLYGON_API_SECRET`，可选填 `POLYGON_PIN`。凭据从 Polygon Settings 生成。保留已有凭据文件，在用户本地编辑敏感值，分享 skill 时仅带空白的 `.env.example`。
2. 使用 [API 调用参考](references/tools.md) 选择操作。优先使用用户提供的 `problemId`。按题名找到多条结果时，用所有者和 ID 消除歧义。新建后记录返回的 ID。编辑已有题时先读取相关工作副本内容，只更改用户要求的部分。
3. 统一题面、约束、样例与代码。用 Polygon LaTeX 编写题面，列清单题及多组数据的总规模限制。准备一份主解（`MA`），以及适合做差分的暴力解和针对典型错误的错解。让 validator 严格校验格式、范围与跨用例限制。用 generator 覆盖最小与最大规模、退化或构造数据、随机数据及触发已知错解的反例。交互题还需准备 interactor 和题面的交互协议。
4. 利用可用的本地编译和小规模差分验证代码，再按用户要求上传文件。先上传文件再绑定 checker、validator 或 interactor。通过手工测试添加样例，并在确认的测试集配置生成脚本。编辑脚本前读出原脚本，保留其他测试并检查编号冲突。查看样例答案、题面渲染和工作副本警告。
5. 在用户授权范围内提交和打包。提交返回冲突时停止后续构建，汇报冲突和工作副本状态。构建时默认开启验题，记录包 ID 并检查最终状态和构建说明。结合逐测试点结果判断错解标签是否符合预期。题包就绪后，按需返回 ZIP 下载链接。
6. 对创建、提交、构建等操作，如果超时或回执含糊，先查询线上状态再决定是否重试。遇到权限、PIN 或限流错误，说明阻塞和已完成的操作，避免重复请求。

交付时给出实际执行范围内的结果。线上编辑报告题目 ID 和变更，提交报告修订，构建报告包 ID、状态及关键失败点。只有收到对应结果才报告提交或验题成功。
