"""把学生获奖用到的证书图归入站点图片目录，并按「赛事-等次-作品」命名。

用法：python tools/extract_award_images.py          # 先导出证书原图
      python tools/collect_student_awards.py       # 再归档、改名

输入：new images/获奖证书原图/证书-pNN-M.png
产物：new images/学生获奖/*.png + tools/student_award_images.json
"""

import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "new images" / "获奖证书原图"
TARGET_DIR = ROOT / "new images" / "学生获奖"
MANIFEST = ROOT / "tools" / "student_award_images.json"

# 证书原图 -> 站点文件名（学生竞赛部分，均已在原图上逐张核对过赛事与等次）
MAPPING = {
    "证书-p35-2.png": "挑战杯创业计划竞赛-全国银奖-逃出生天.png",
    "证书-p32-1.png": "中国国际互联网+大赛-全国金奖-白色森林儿童美术.png",
    "证书-p32-2.png": "中国国际互联网+大赛-全国银奖-跃晟香蕉.png",
    "证书-p32-3.png": "中国国际互联网+大赛-全国铜奖-蚕燃一新智能蚕茧烤房.png",
    "证书-p37-1.png": "全国大学生职业规划大赛-全国银奖-欧阳丝钰.png",
    "证书-p37-2.png": "全国大学生职业规划大赛-全国铜奖-孟文轩.png",
}
# 已有（或用户直接提供原图）的证书与照片，一并登记进清单
EXISTING = [
    "new images/学生获奖/大创赛2025-全国银奖-源启星链.jpg",
    "new images/学生获奖/大创赛2025-全国铜奖-神机妙用水稻除草机.jpg",
    "new images/学生获奖/大创赛2025-全国铜奖-智眸茧芯.jpg",
    "new images/廖奎源职规国金通知.png",
    "new images/大创赛合照.jpg",
    "new images/职规赛合照.jpg",
]


def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source_name, target_name in MAPPING.items():
        source = SOURCE_DIR / source_name
        if not source.exists():
            print("跳过（源文件不存在）：%s，请先运行 tools/extract_award_images.py" % source_name)
            continue
        target = TARGET_DIR / target_name
        shutil.copyfile(source, target)
        manifest.append({
            "文件": "new%20images/学生获奖/" + target_name,
            "源文件": source_name,
            "字节": target.stat().st_size,
        })
        print("已归入 %s（%.0f KB）" % (target.name, target.stat().st_size / 1024))
    for relative in EXISTING:
        path = ROOT / relative
        if path.exists():
            manifest.append({
                "文件": relative.replace("new images/", "new%20images/").replace(" ", "%20"),
                "说明": "申报材料中已有图片",
                "字节": path.stat().st_size,
            })
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("清单写入 %s，共 %d 项" % (MANIFEST.name, len(manifest)))


if __name__ == "__main__":
    main()
