# rk-build

ATK-DLRK3568（RK3568）Linux 6.1 SDK 的编译 / 打包 skill。

## 它解决什么

这个 SDK 的编译流程有几个**不看代码就想不到**的坑，踩过一次都记在这里：

- 必须先选板级配置，否则 `build.sh` 进交互菜单，没法自动化
- `menuconfig` 改的东西**每次编译都会被覆盖**（`.config` 从 defconfig 重新生成）
- 改了 buildroot 配置，SDK **不会**自动清残留，旧包文件会混进固件
- 宿主机缺 `gettext` 会卡在 rootfs 阶段（`Your msgmerge is missing`）
- 长的编译必须用 `setsid` 脱离 SSH 会话，否则断网就死
- 监控要盯**宿主机** E: 盘，客户机的 `df` 是假的（vdisk 超配）

## 内容

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 主流程：连虚拟机 → 选板级配置 → 编译 → 监控空间 → 产物 → 坑 |
| `references/config-customization.md` | buildroot 配置定制详解：三层结构、怎么加减软件包、怎么验证、残留怎么清、片段速查表 |

## 典型用法

```
编译一下 RK 的大包          → 走 SKILL.md 第二、三节
关掉 qt 和 opencv           → 走 references/config-customization.md
编译卡住了 / 报错           → 先看 SKILL.md 第五节「四个坑」
虚拟机 SSH 连不上           → SKILL.md 第零节（多半是 IPv4 掉了，按 MAC 找新 IP）
```

## 现状备注（2026-09-27）

Qt5 / OpenCV4 / Chromium / Weston / LVGL 已在 `buildroot/configs/alientek_rk3568_defconfig` 里关闭，以后编译自动生效。内核已迁到 `SP-Melokc/RK3568-Kernel6.1` 独立管理，不受厂商 repo 同步影响。
