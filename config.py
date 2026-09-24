from pathlib import Path
from typing import Iterable, Optional


def write_sumocfg(
    outdir: Path,
    net: Path,
    routes: Path,
    step_length: float = 1.0,
    additionals: Optional[Iterable[Path]] = None,
    begin: float = 0.0,
    end: Optional[float] = None,
    time_to_teleport: Optional[float] = None,
) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    cfg_path = outdir / "scenario.sumocfg"

    additional_str = ""
    if additionals:
        rel_names = ",".join(p.name for p in additionals)
        additional_str = f'<additional-files value="{rel_names}"/>'

    begin_tag = f'<begin value="{begin}"/>' if begin is not None else ""
    end_tag = f'<end value="{end}"/>' if end is not None else ""
    ttt_tag = f'<time-to-teleport value="{time_to_teleport}"/>' if time_to_teleport is not None else ""

    cfg_xml = f"""<configuration>
  <input>
    <net-file value="{net.name}"/>
    <route-files value="{routes.name}"/>
    {additional_str}
  </input>
  <time>
    {begin_tag}
    {end_tag}
    <step-length value="{step_length}"/>
  </time>
  <processing>
    {ttt_tag}
  </processing>
</configuration>
"""
    cfg_path.write_text(cfg_xml, encoding="utf-8")
    print(f"[config] Wrote {cfg_path}")
    return cfg_path

