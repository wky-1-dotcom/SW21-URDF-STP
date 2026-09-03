# 越疆RC7AS机械臂模型（SW21）＋大寰电动二指夹爪（165-90）＋URDF文件

本仓库保存越疆的RC7AS机械臂的 SolidWorks 装配体+电动二指夹爪和 STEP 通用模型，
用于机械结构查看、模型转换以及后续 ROS 2 / URDF 开发。

## 模型预览


[机械臂模型预览](Images/000.png)

## 文件内容

| 文件或目录 | 说明 |
|---|---|
| `SolidWorks/` | SolidWorks 原始装配体或 Pack and Go 压缩包 |
| `STEP/` | STEP 通用三维模型 |
| `Images/` | 模型预览图片 |
| `README.md` | 项目说明文件 |

## 模型信息

- 模型名称：机械臂+末端执行器
- 建模软件：SolidWorks 2021
- 模型类型：机械臂装配体+电动二指夹爪
- 通用格式：STEP
- 自由度：6-DOF
- 长度单位：mm
- 质量：由于具体材质不知，质量大概复原为24kg
- 用途：ROS 2、URDF、Gezabo 机械结构设计和运动仿真

## 文件说明

### SolidWorks 装配体

SolidWorks 文件使用 Pack and Go 功能进行打包，压缩包中应包含：

- `.SLDASM` 装配体文件
- `.SLDPRT` 零件文件


使用方法：

1. 下载 SolidWorks 装配体压缩包。
2. 将压缩包完整解压到同一个文件夹。
3. 保持解压后的目录结构不变。
4. 使用 SolidWorks 2021 或2021以上的版本打开 `.SLDASM` 文件。

### STEP 模型

STEP 文件可用于其他 CAD 软件查看或转换，例如：

- SolidWorks
- FreeCAD
- Fusion 360
- Inventor
- Creo

STEP 格式通常只保存实体和装配结构，保留有原始特征树、配合关系和材料信息。

## 下载方法

点击仓库页面右上方的：

`Code -> Download ZIP`

也可以单独进入文件页面下载所需模型。

对于 Git LFS 管理的大文件，建议克隆整个仓库：

```bash
git lfs install
git clone https://github.com/wky-1-dotcom/SW21-URDF-STP.git
