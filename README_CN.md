# cc-planbar

[English](README.md)

Claude Code 状态栏组件：显示第三方 coding plan 供应商（Kimi、智谱 GLM 等）的套餐额度。

在底部状态栏显示：**Context 使用百分比 + 当前 provider 的套餐额度**（5 小时窗口 / 周限额，含重置时间），按用量变色：绿 <60%，黄 60–84%，红 ≥85%。

```
Model: k3 | Ctx 24.0% | Kimi 5h 15% (rst 03:44) · week 69% (rst 07/31 05:44)
```

额度查询参考 CC Switch 的实现，按 `ANTHROPIC_BASE_URL` 自动识别 provider：

| base_url 包含 | provider | 接口 |
|---|---|---|
| `api.kimi.com/coding` | Kimi | `GET /coding/v1/usages`（Bearer） |
| `bigmodel.cn` / `api.z.ai` | 智谱 GLM | `GET /api/monitor/usage/quota/limit`（无 Bearer 前缀） |

额度接口 5 分钟缓存一次；切 provider 后旧缓存自动失效。

## 适用环境

- **必需**：Claude Code + Node.js。渲染依赖 [ccstatusline](https://github.com/sirmalloc/ccstatusline)，cc-planbar 作为它的 custom-command widget 运行
- **适用**：通过 `ANTHROPIC_BASE_URL` 使用第三方 coding plan 供应商的用户（目前直接支持 Kimi For Coding、智谱 GLM 国内/国际站；其它供应商可参照 `zhipu()` 加一个函数并注册到 `PROVIDERS`，快速实现）。与切换方式无关——CC Switch、手动改配置或其他工具均可，只要 `~/.claude/settings.json` 里的 base URL 指向上述供应商
- **可选**：`fix-cc-switch.sh` 仅在使用 [CC Switch](https://github.com/farion1231/cc-switch) 切换 provider 时需要，不用可忽略

## 文件

| 文件 | 安装到 |
|---|---|
| `quota-status.py` | `~/.claude/scripts/quota-status.py` |
| `ccstatusline-settings.json` | `~/.config/ccstatusline/settings.json` |
| `fix-cc-switch.sh` | 只用 CC Switch 时才需要，直接跑一次 |

## 安装步骤

```bash
# 1. 安装 statusline 渲染器（需要 Node.js）
npm install -g ccstatusline

# 2. 拷贝文件
mkdir -p ~/.claude/scripts ~/.config/ccstatusline
cp quota-status.py ~/.claude/scripts/
cp ccstatusline-settings.json ~/.config/ccstatusline/settings.json
chmod +x ~/.claude/scripts/quota-status.py
```

然后编辑 `~/.claude/settings.json`，顶层加上：

```json
"statusLine": {
  "type": "command",
  "command": "ccstatusline"
}
```

重启 Claude Code 生效。

## 如果用 CC Switch 切换 provider

CC Switch 切换时会把 `~/.claude/settings.json` 重写成「provider env + 公共配置快照」，快照里没有 `statusLine` 的话状态栏会消失。跑一次修复脚本（把 statusLine 注入它的快照）：

```bash
bash fix-cc-switch.sh
```

之后**重启 CC Switch 应用**再切 provider。

## 常见问题

**CC Switch 升级后，fix-cc-switch.sh 的修复会失效吗？**

不会。原因有二：

1. 修复写入的是 CC Switch 的用户数据目录（`~/.cc-switch/cc-switch.db`），应用升级只替换程序本体，不会动数据库，也不会重跑已完成的迁移
2. 即使 CC Switch 日后重新从 live `settings.json` 抓取公共配置快照，只要当时的 `settings.json` 里有 `statusLine`（装完本状态栏后就有），抓到的快照也会带上它

**在 CC Switch 界面手动编辑/重置了公共配置，状态栏又消失了怎么办？**

重新跑一遍 `bash fix-cc-switch.sh`，然后重启 CC Switch 应用即可。该脚本可重复执行，无副作用（每次执行前会自动备份数据库为 `cc-switch.db.bak-statusline`）。

## 备注

- 颜色阈值想改：编辑 `quota-status.py` 里的 `col()` 函数
- 月度额度：Kimi 接口的 `totalQuota` 字段有值时会自动显示 `month X%`

## 致谢

- [ccstatusline](https://github.com/sirmalloc/ccstatusline) — 状态栏渲染器，本项目作为其 custom-command widget 运行
- [CC Switch](https://github.com/farion1231/cc-switch) — 各供应商的额度接口与检测逻辑参考自其 `coding_plan.rs` 实现
