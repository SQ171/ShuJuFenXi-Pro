"""MET-V6 测试台 CSV 解析器 — 复用改造自 0522数据处理软件-bate/parser.py"""

import os
import re
import pandas as pd
from .base import BaseParser
from core.models import ParsedData
from core.constants import NUMERIC_COLUMNS


class METV6Parser(BaseParser):
    def can_parse(self, filepath: str) -> bool:
        if not filepath.lower().endswith(".csv"):
            return False
        with open(filepath, "r", encoding="utf-8-sig") as f:
            head = f.read(1024)
        return "MET-V6" in head

    def parse(self, filepath: str) -> ParsedData:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            raw = f.read()
        metadata = self._parse_metadata(raw)
        df = self._parse_data(raw)
        return ParsedData(metadata=metadata, df=df)

    def _parse_metadata(self, raw: str) -> dict:
        patterns = {
            "测试台型号": r"测试台型号:,*\s*([^,\n]*)",
            "测试台编号": r"测试台编号:,*\s*([^,\n]*)",
            "拉力方向": r"拉力方向:,*\s*([^,\n]*)",
            "扭矩方向": r"扭矩方向:,*\s*([^,\n]*)",
            "环境温度": r"环境温度:,*\s*([^,\n]*)",
            "环境湿度": r"环境湿度:,*\s*([^,\n]*)",
            "大气压": r"大气压:,*\s*([^,\n]*)",
            "空气密度": r"空气密度:,*\s*([^,\n]*)",
            "测试时间": r"测试时间:,*\s*([^,\n]*)",
            "桨直径": r"桨直径:,*\s*([^,\n]*)",
            "测试模式": r"测试模式:,*\s*([^,\n]*)",
            "日志记录速率": r"日志记录速率:,*\s*([^,\n]*)",
            "采集速率": r"采集速率:,*\s*([^,\n]*)",
        }
        unit_strip = {
            "环境温度": "℃",
            "环境湿度": "%RH",
            "空气密度": "kg/m³",
            "大气压": "kPa",
        }
        metadata = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, raw)
            if match:
                value = match.group(1).strip()
                if key in unit_strip:
                    value = value.replace(unit_strip[key], "").strip()
                metadata[key] = value
        return metadata

    def _parse_data(self, raw: str) -> pd.DataFrame:
        lines = raw.strip().split("\n")
        header_idx = None
        for i, line in enumerate(lines):
            if "帧数" in line and "油门" in line:
                header_idx = i
                break
        if header_idx is None:
            return pd.DataFrame()

        columns = [col.strip() for col in lines[header_idx].split(",")]
        rows = []
        for line in lines[header_idx + 1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < len(columns):
                continue
            rows.append([p.strip() for p in parts])

        df = pd.DataFrame(rows, columns=columns)
        for col in columns:
            if col in NUMERIC_COLUMNS:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "帧时间" in columns:
            df["帧时间"] = pd.to_datetime(df["帧时间"], errors="coerce")
        return df


def parse_filename(filepath: str) -> dict:
    """从文件名解析测试变量"""
    FIELD_NAMES = [
        "日期", "桨叶转向", "电机型号", "桨叶材质", "批次", "桨叶序号", "运行序号",
        "涵道型号", "涵道唇口半径", "涵道延伸段长度", "涵道延伸段角度", "涵道间隙",
    ]
    basename = os.path.splitext(os.path.basename(filepath))[0]
    parts = basename.split("-")
    result = {}
    for i, name in enumerate(FIELD_NAMES):
        result[name] = parts[i].strip() if i < len(parts) else None
    return result
