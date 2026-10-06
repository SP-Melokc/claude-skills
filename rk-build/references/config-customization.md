# buildroot 配置定制（加减软件包）

## 一、配置的三层结构

```
buildroot/configs/alientek_rk3568_defconfig          ← 板级主配置（入口）
   ├─ #include "base/base.config"                     ← 片段（可多层 include）
   ├─ #include "chips/rk3566_rk3568_aarch64.config"
   ├─ #include "gui/qt5.config"
   └─ ...（本板共 26 个 include）
                    ↓ 每次编译时合并
buildroot/output/alientek_rk3568/.config             ← 最终配置（buildroot 用这个编）
```

**片段的真实位置**：`buildroot/configs/rockchip/` 下。主配置里写 `#include "gui/qt5.config"`，实际解析到 `buildroot/configs/rockchip/gui/qt5.config`。

## 二、⚠️ 核心坑：不要用 menuconfig

`device/rockchip/common/scripts/mk-buildroot.sh` 里有一行**每次编译都无条件执行**：

```bash
make -C "$BUILDROOT_DIR" O="$BUILDROOT_OUTPUT_DIR" ${BUILDROOT_BOARD}_defconfig
```

`.config` 每次都从 defconfig 重新生成 → **menuconfig 的改动下一次编译就被覆盖**。

要**永久**生效，只能改 defconfig 或它 include 的片段。

## 三、怎么找某个包是谁开的

```bash
R=~/atk_dlrk3568_linux6.1_sdk/atk_dlrk3568_linux6.1/buildroot/configs/rockchip
grep -rn "BR2_PACKAGE_OPENCV4=y" $R                    # 在哪个片段里
grep -n "BR2_PACKAGE_" $R/gui/qt5.config               # 某个片段开了啥
```

## 四、怎么关掉一个包（三种情况）

**情况 1：整个片段都不想要 → 注释掉 include**

主配置里：
```
# #include "gui/qt5.config"
```
（前面再加一个 `#` 即可，buildroot 忽略 `#` 开头的行）

**情况 2：片段里只要去掉其中几个 → 删掉/注释那几行**

直接编辑片段文件，把不想要的 `BR2_PACKAGE_xxx=y` 注释掉或删掉。

**情况 3：包直接写在主配置里 → 删掉那几行**

比如 OpenCV4 的 23 行就直接写在 `alientek_rk3568_defconfig` 里。

**依赖要一并处理**：被关掉的包如果被别的项依赖（`depends on`），Kconfig 会自动把它关掉；但如果是 `select` 关系，可能反向把包又拉回来。改完**必须验证**（见第五节）。

## 五、验证（必做）

编译启动后约 **1 分钟**内，buildroot 就会重新生成 `.config`，此时检查：

```bash
C=~/atk_dlrk3568_linux6.1_sdk/atk_dlrk3568_linux6.1/buildroot/output/alientek_rk3568/.config
grep -E "^(# )?BR2_PACKAGE_(QT5|OPENCV4|WESTON|LVGL|CHROMIUM)(=| is not set)" $C
```

期望看到 `# BR2_PACKAGE_QT5 is not set` 这种形式。若仍是 `=y`，说明被别的包 `select` 拉回来了，要顺着依赖继续关。

编译进程别等太久才验；确认无误再放它跑。

## 六、⚠️ 残留：改了配置不等于固件干净

buildroot **不会**因为配置里去掉了某个包，就把已经装进 `target/` 的文件删掉。SDK 也只打印一行提示（**只是文字，不会执行**）：

```
Buildroot config changed!
You might need to clean it before building:
rm -rf .../buildroot/output/alientek_rk3568
```

**两条路：**

| 做法 | 代价 | 结果 |
|---|---|---|
| `rm -rf buildroot/output/alientek_rk3568` 后重编 | **全量重编**（约 2~2.5h；`buildroot/dl/` 下载缓存保留，不重下）| 绝对干净 |
| 手动删 `target/` 里的残留再续编 | 快 | 干净（需自己确认删全了）|

手动清理示例：

```bash
T=~/atk_dlrk3568_linux6.1_sdk/atk_dlrk3568_linux6.1/buildroot/output/alientek_rk3568/target
find $T \( -iname "*qt5*" -o -iname "*opencv*" -o -iname "*weston*" -o -iname "*lvgl*" \) -exec rm -rf {} +
```

清理后**要复验**编译结束时 `target/` 里这些包的文件数是否为 0。

> 注意：`/opt/ui`（预编译 Qt 程序，68M）来自 **overlay**（`buildroot/board/alientek/atk-dlrk3568/fs-overlay/`），**不受 buildroot 配置控制**，会被重新打进固件。要去掉得改 overlay。

## 七、本次实例（2026-09-27 关闭 Qt5/OpenCV/Chromium/Weston/LVGL）

改的文件：`buildroot/configs/alientek_rk3568_defconfig`

```
# 注释掉 4 个 include
# #include "network/chromium.config"
# #include "gui/weston.config"
# #include "gui/lvgl.config"
# #include "gui/qt5.config"

# 删除 25 行
BR2_PACKAGE_LIBCONNMAN_QT=y          # 依赖 Qt
BR2_PACKAGE_OPENCV4*=y ...（23 行）
BR2_PACKAGE_WESTON_VNC=y             # 依赖 weston
```

注意 `network/chromium.config` 里其实**没有** `BR2_PACKAGE_CHROMIUM=y`，只有 `CHROMIUM_WAYLAND` 和 cairo/pango/jpeg-turbo 等依赖——所以 Chromium 本体本来就没编。

## 八、常用片段速查

主配置当前 include 的 26 个：

`base/base` · `bus/{can,pci}` · `chips/rk3566_rk3568_aarch64` · `font/chinese` · `fs/{exfat,ntfs,vfat}` · `gpu/mali` · `multimedia/audio` · `multimedia/camera` · `multimedia/gst/{audio,camera,rtsp,video}` · `multimedia/mpp` · `wifibt/{bt,wireless}` · `tools/{benchmark,common,test}` · `network/chromium` · `ai/npu2` · `gui/{weston,lvgl,qt5}`

**没 include 但可用的**（想加就在主配置里加一行 `#include`）：

| 片段 | 用途 |
|---|---|
| `ai/rkai.config`、`ai/rknn-llm.config` | RKAIQ / RKNN-LLM |
| `fs/{btrfs,cifs,e2fs,f2fs,nfs,ubifs}.config` | 各种文件系统支持 |
| `gpu/mesa3d.config` | Mesa3D |
| `gui/x11.config` | X11 |
| `gui/lvgl/*`（v8/v9、drm/rkadk/sdl）| LVGL 各版本/后端 |
| `multimedia/{libcamera,rockit}.config` | libcamera / rockit |
| `network/network.config` | 网络配置 |
| `tools/{extra,gdb,perf}.config` | 额外工具 / gdb / perf |
| `products/{electric,ipc}.config`、`products/mos/graphic.config` | 产品预设 |
| `security/{cve,tee_*}.config` | 安全相关 |
| `toolchain/*` | 交叉工具链选择 |
| `ros2_dep.config` | ROS2 依赖 |

recovery 用的 `alientek_rk3568_recovery_defconfig` 只 include 三个片段（`base/base`、`base/recovery`、`chips/rk3566_rk3568_aarch64`），很干净，一般不需要动。
