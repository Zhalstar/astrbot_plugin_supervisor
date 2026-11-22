
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_supervisor?name=astrbot_plugin_supervisor&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_supervisor

_✨ 赛博监工 ✨_  

[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-4.13%2B-orange.svg)](https://github.com/Soulter/AstrBot)

</div>

## 🤝 介绍

赛博监工，检测到某人水群，就提醒他滚去干活

## 📦 安装

在astrbot的插件市场搜索astrbot_plugin_supervisor，点击安装即可

## ⚙️ 配置

### 插件配置

请在astrbot面板配置，插件管理 -> astrbot_plugin_supervisor -> 操作 -> 插件配置：

可在“图片回复 -> 监工图片”配置项中上传一张或多张自定义图片。插件会从已上传且仍然存在的图片中随机选择，不再读取插件目录内的 `image` 文件夹。

图片回复、LLM 回复和戳一戳分别拥有独立配置组，并使用权重随机触发。触发概率为对应权重除以所有正权重之和；将某项权重设置为 `0` 即可禁用该响应。

## 使用说明

|     命令      |      说明       |
|:-------------:|:-----------------------------:|
| 监督@某人      | 将某人加进监督名单里  |
| 解除监督@某人  | 将某人移出监督名单里   |
| 监督列表       | 查看当前监督名单及剩余时长 |

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561（不点star不给进）
