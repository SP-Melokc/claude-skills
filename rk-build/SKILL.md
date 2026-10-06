---
name: rk-build
description: 编译/打包正点原子 ATK-DLRK3568 Linux 6.1 SDK（RK3568）。覆盖板级配置选择、全量/单项编译、脱离 SSH 会话的长时编译、宿主机磁盘空间监控、buildroot 配置定制（关掉不要的包），以及 4 个已踩过的坑（menuconfig 被覆盖、残留不进 target、缺 gettext、recovery 二次编译）。Trigger on: "编译RK SDK", "编译大包", "build.sh", "rk3568 编译", "重新编内核", "打固件", "update.img", "关掉 qt/opencv", "build the RK SDK".
---

# RK3568 SDK 编译与打包

目标 SDK：正点原子 **ATK-DLRK3568 Linux 6.1**，位于 alientek 虚拟机内：

```
~/atk_dlrk3568_linux6.1_sdk/atk_dlrk3568_linux6.1/
```

用户是 Master（ARM64 BSP 工程师）。下面所有操作用 `ssh alientek@<VM_IP> '<cmd>'` 在虚拟机里执行。

---

## 零、先确认能连上虚拟机

虚拟机是**桥接 + DHCP，IPv4 会不定期掉线**（只剩 IPv6）。SSH 连不上时，**先按 MAC 找它当前 IP**，别急着以为网络断了：

```bash
# 宿主机（Windows Git Bash）上扫一遍同网段填充 ARP
for i in $(seq 1 254); do /c/Windows/System32/PING.EXE -n 1 -w 150 10.124.236.$i >/dev/null 2>&1 & done; wait
/c/Windows/System32/ARP.EXE -a | grep -i "00-0c-29"     # 虚拟机的 MAC
```

掉线后在**虚拟机控制台**恢复：

```bash
sudo dhclient -r ens33 && sudo dhclient -v ens33
ip -4 addr show ens33        # 确认拿回 IPv4（不一定是原地址）
```

---

## 一、选板级配置（必须先做，否则进交互菜单）

```bash
cd ~/atk_dlrk3568_linux6.1_sdk/atk_dlrk3568_linux6.1
./build.sh 01_atk_dlrk3568_automipi_hdmi_defconfig
```

选中的结果落成软链 `output/defconfig`。**不选的话 `./build.sh` 会弹交互菜单**，无法自动化。

可选板级配置（在 `device/rockchip/.chips/rk3566_rk3568/`）：

| 配置 | 用途 |
|---|---|
| `01_atk_dlrk3568_automipi_hdmi_defconfig` | **出厂固件配置**（MIPI 屏自适应 + HDMI），默认选它 |
| `02/03/04_...mipi{720x1280,800x1280,1080x1920}_hdmi` | 指定 MIPI 分辨率 |
| `05_...lvds1280x800_hdmi` | LVDS 1280x800 |
| `06_...edp` | eDP 接口 |
| `07_...hdmi` | 纯 HDMI |
| `08/09_...ubuntu_panfrost_*` | Ubuntu 根文件系统（**不是 buildroot**）|

---

## 二、编译

```bash
# 全量：u-boot + 内核 + 主 rootfs + recovery + 固件打包（默认目标 all）
setsid ./build.sh > /tmp/rkbuild.log 2>&1 < /dev/null &

# 单项
./build.sh kernel        # 只编内核（也可写 kernel-6.1）
./build.sh uboot         # 只编 u-boot
./build.sh buildroot     # 只编主根文件系统
./build.sh firmware      # 只打包固件
./build.sh recovery      # 只编 recovery
```

**必须用 `setsid`。** 虚拟机网络不稳，SSH 一断，普通 `nohup ... &` 仍可能被 SIGHUP 杀掉；`setsid` 让它彻底脱离会话，断网也照跑。

日志同时会存到 `output/sessions/<时间戳>/`。

**耗时参考**：全量约 **4 小时**（12 核）。主 rootfs 约 2~2.5h，recovery 约 0.5~1h。

---

## 三、监控磁盘（盯宿主机，不是客户机！）

编译期间**必须盯宿主机的 E: 盘**——客户机 `df` 显示的几百 G 可用是**假的**（vmdk 超配，见虚拟机磁盘超配那条坑）。

```bash
df -h /e        # 宿主机 E:（Git Bash 里 /e 就是 E:），虚拟机磁盘全在这块盘上
```

预警线 **15G**。低于就**冻结整个编译进程组**（可恢复，比杀掉安全）：

```bash
PGID=$(ps -o pgid= -p $(pgrep -f build.sh | head -1))
kill -STOP -$PGID        # 冻结
kill -CONT -$PGID        # 恢复
```

监控脚本**要能区分「SSH 连不上」和「编译已结束」**——用 ssh 的**退出码**判断，不要用「输出为空」判断，否则网络一抖就误报编译结束。

实测消耗比：虚拟机内写入 40G，宿主机 E: 只掉约 10G（死块复用），所以空间通常很宽裕，但**仍要盯**。

---

## 四、产物

全部在 `output/firmware/`：

| 文件 | 说明 |
|---|---|
| **`update.img`** | **整包烧写镜像**（瑞芯微工具一键刷机），约 1.2G |
| `boot.img` | 内核 |
| `rootfs.img` | 主根文件系统（指向 `buildroot/output/alientek_rk3568/images/rootfs.ext2`）|
| `uboot.img` / `MiniLoaderAll.bin` | 引导 |
| `recovery.img` | 恢复系统 |
| `oem.img` / `userdata.img` / `misc.img` / `parameter.txt` | 分区 |

---

## 五、四个坑（都踩过，别重复）

1. **`menuconfig` 的改动会被覆盖**
   `mk-buildroot.sh` **每次编译都无条件**执行 `make ... <board>_defconfig` 重新生成 `.config`。
   → 要**永久**改配置，必须改 `buildroot/configs/alientek_rk3568_defconfig`，或它 `#include` 的片段（片段在 `buildroot/configs/rockchip/` 下，如 `gui/qt5.config`）。

2. **改完配置后 SDK 不会自动清理**
   它只打印一行提示：`You might need to clean it before building: rm -rf .../output/<board>` —— **这只是提示文字，不会真执行**。
   → 直接续编的话，之前已装进 `target/` 的包文件会**留在最终固件里**。要干净就得手动删残留，或整个 `rm -rf buildroot/output/alientek_rk3568` 重编（代价是全量重编，`dl/` 下载缓存会保留）。

3. **宿主机缺 `gettext`** → rootfs 阶段挂掉，报 `Your msgmerge is missing`
   因为配置开了 `BR2_SYSTEM_ENABLE_NLS=y`。修：`sudo apt-get install -y gettext`。
   注意 SDK 文档给的那一大串依赖里，其它包（gawk/bison/flex/fakeroot/cmake/dtc/python2/rsync…）通常**早就装好了**，通常只缺 gettext。

4. **会编两遍 buildroot**
   主 rootfs（`output/alientek_rk3568`）+ **recovery 恢复系统**（`output/alientek_rk3568_recovery`）。recovery 走**另一个配置** `alientek_rk3568_recovery_defconfig`（只含 base + recovery + chip 三个片段，很干净），**改主配置管不到它**。它有自己的输出目录，所以 host 工具链要重编一遍，是后半程耗时的主因。

---

## 六、定制 buildroot（加/减软件包）

**不要用 menuconfig**（见坑 1）。直接改配置文件，方法见 `references/config-customization.md`。

**当前已关闭**（2026-09-27）：Qt5 / OpenCV4 / Chromium / Weston / LVGL。

> 副作用提醒：去掉 Qt5 + Weston 后，**板子出厂 UI（`/opt/ui/systemui`、`controlcenter`，预编译 Qt 程序）跑不起来**，等于没有图形界面。`/opt/ui` 那 68M 预编译程序仍在 overlay 里、会被打进固件（属于 overlay，不受 buildroot 配置控制）。

---

## 七、与内核仓库的关系

内核已**脱离厂商 repo 管理**，改由 Master 自己的 GitHub（`SP-Melokc/RK3568-Kernel6.1`，分支 main）独立管理：

- 通过 `.repo/local_manifests/kernel-custom.xml` 里的 `remove-project` 让 `repo sync` **不再碰 `kernel-6.1`**
- 内核改动直接在 `kernel-6.1/` 里 `git add/commit/push`
- `./build.sh kernel` 编的就是这份内核
