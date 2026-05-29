"""Pipeline S1: 批量加载 CSV → list[TestRun] + unified_df"""

import os
import pandas as pd
from core.models import TestRun
from core.constants import COL_SOURCE_FILE
from core.air_density import correction_factor, parse_env_from_metadata
from parsers.registry import ParserRegistry
from parsers.metv6 import parse_filename
from analysis.pipeline import AnalysisContext


def load_data(ctx: AnalysisContext) -> AnalysisContext:
    runs = []
    dfs = []

    for filepath in ctx.file_paths:
        parser = ParserRegistry.get_parser(filepath)
        if parser is None:
            continue

        parsed = parser.parse(filepath)
        file_info = parse_filename(filepath)
        filename = os.path.basename(filepath)

        df = parsed.df
        df[COL_SOURCE_FILE] = filename

        temp_c, pressure_hpa, rh_pct = parse_env_from_metadata(parsed.metadata)
        cf = correction_factor(temp_c, pressure_hpa, rh_pct)

        if "系统力效-g/W" in df.columns:
            df["系统力效-g/W"] = df["系统力效-g/W"] * cf
        if "拉力-g" in df.columns:
            df["拉力-g"] = df["拉力-g"] * cf

        dfs.append(df)

        start_time = df["帧时间"].iloc[0] if "帧时间" in df.columns else None
        end_time = df["帧时间"].iloc[-1] if "帧时间" in df.columns else None
        duration = (end_time - start_time).total_seconds() if start_time and end_time else 0.0

        runs.append(TestRun(
            filename=filename,
            filepath=filepath,
            file_info=file_info,
            metadata=parsed.metadata,
            df=df,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            correction_factor=cf,
        ))

    unified_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    ctx.test_runs = runs
    ctx.unified_df = unified_df
    return ctx
