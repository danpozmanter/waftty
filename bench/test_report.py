"""Tests of report.py against each results schema it reads.

    uv run python -m unittest test_report
"""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

import report

TIMES = {"tp_plain": [392.8, 386.9], "tp_sgr": [524.7], "tp_unicode": [441.3]}


def mac_sample(footprint, cpu):
    return {"footprint": footprint, "rss": footprint * 2, "cpu": cpu, "processes": {"t": footprint}}


def mac_terminal(idle=36.4, heavy=53.1, seconds=1.7):
    return {"ram_idle": [mac_sample(idle, 0.0)], "ram_heavy": [mac_sample(heavy, seconds)], **TIMES}


def linux_sample(pss, cpu):
    return {"pss": pss, "uss": pss - 1, "rss": pss + 5, "vram": 0, "xserver": 0.0, "cpu": cpu}


def linux_terminal(pss=15.2):
    return {"ram_idle": [linux_sample(pss, 0.0)], "ram_heavy": [linux_sample(pss + 10, 0.4)],
            **TIMES, "cpu_idle": [0.25], "cpu_load": [{"percent": 138.6, "seconds": 0.35}],
            "latency": [1.0, 2.0], "streaming": {"latency": [3.0], "gaps": [16.0, 17.0]},
            "startup": [100.0]}


class Report(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.dir = Path(folder.name)
        self.out = self.dir / "report"

    def run_report(self, system, results):
        path = self.dir / "results.json"
        path.write_text(json.dumps(results))
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            report.main([system, "--results", str(path), "--out", str(self.out)])
        return (self.out / "RESULTS.md").read_text(), err.getvalue()

    def refused(self, system, results):
        with self.assertRaises(SystemExit) as caught:
            self.run_report(system, results)
        return str(caught.exception)

    def charts(self):
        return {p.stem for p in self.out.glob("*.png")}

    def test_a_mac_run_that_stopped_early_reports_footprint_and_print_seconds(self):
        text, err = self.run_report("mac", {"waftty": mac_terminal(), "kitty": mac_terminal(90.0, 120.0, 3.5)})
        self.assertEqual(self.charts(), {"ram", "cpu", "throughput"})
        self.assertIn("Idle footprint", text)
        self.assertIn("| waftty | 36.4 MiB | 72.8 MiB | 53.1 MiB | 106.2 MiB |", text)
        self.assertIn("| waftty | - | - | 1.70 s |", text)
        self.assertNotIn("PSS", text)
        self.assertNotIn("None", text)
        self.assertIn("idle CPU for waftty, kitty", err)
        self.assertIn("uv run mac/bench.py run --only cpu", err)

    def test_a_finished_mac_run_reads_its_cpu_runs(self):
        terminal = mac_terminal()
        terminal.update(cpu_idle=[0.5], cpu_load=[{"percent": 90.0, "seconds": 2.25}])
        text, _ = self.run_report("mac", {"_meta": {"platform": "macos", "scrollback": 10000, "os": "15.1"},
                                          "waftty": terminal})
        self.assertIn("| waftty | 0.50% | 90% | 2.25 s |", text)
        self.assertIn("macOS 15.1, scrollback 10000", text)
        self.assertNotIn("heavy memory runs", text)

    def test_a_linux_run_reports_pss_and_every_chart(self):
        text, err = self.run_report("linux", {"_meta": {"platform": "linux", "scrollback": 10000},
                                              "waftty": linux_terminal()})
        self.assertEqual(self.charts(), {"ram", "cpu", "throughput", "latency", "smoothness", "startup"})
        self.assertIn("Idle PSS", text)
        self.assertIn("| waftty | 15.2 MiB | 14.2 MiB | 25.2 MiB | 24.2 MiB |", text)
        self.assertIn("| waftty | 0.25% | 139% | 0.35 s |", text)
        self.assertEqual(err, "")

    def test_older_linux_results_without_meta_or_secondary_figures_report(self):
        terminal = linux_terminal()
        for phase in ("ram_idle", "ram_heavy"):
            terminal[phase] = [{"pss": r["pss"]} for r in terminal[phase]]
        text, _ = self.run_report("linux", {"waftty": terminal})
        self.assertIn("| waftty | 15.2 MiB | - | 25.2 MiB | - |", text)
        self.assertIn("records no details", text)

    def test_a_sample_without_the_systems_memory_figure_is_refused_by_name(self):
        terminal = mac_terminal()
        del terminal["ram_heavy"][0]["footprint"]
        message = self.refused("mac", {"waftty": terminal})
        self.assertIn("ram_heavy sample of waftty has no footprint", message)
        self.assertIn("--only ram", message)

    def test_mixed_memory_figures_are_refused_and_not_compared(self):
        message = self.refused("mac", {"waftty": mac_terminal(), "guake": linux_terminal()})
        self.assertIn("guake has no footprint", message)

    def test_results_from_the_other_system_are_refused(self):
        message = self.refused("linux", {"_meta": {"platform": "macos"}, "waftty": mac_terminal()})
        self.assertIn("results from macos", message)

    def test_a_terminal_without_memory_is_named_and_the_others_report(self):
        text, err = self.run_report("mac", {"waftty": mac_terminal(), "kitty": dict(TIMES)})
        self.assertIn("memory for kitty", err)
        self.assertNotIn("| kitty | -", text.split("## Throughput")[0])

    def test_incomplete_cpu_shows_a_dash_and_no_zero(self):
        partial = mac_terminal()
        partial["cpu_idle"] = [0.5]
        text, err = self.run_report("mac", {"waftty": partial, "kitty": mac_terminal(90.0, 120.0, 3.5)})
        self.assertIn("| waftty | 0.50% | - | 1.70 s |", text)
        self.assertIn("| kitty | - | - | 3.50 s |", text)
        self.assertIn("idle CPU for kitty", err)
        self.assertIn("cpu", self.charts())

    def test_samples_with_no_cpu_at_all_leave_the_chart_out(self):
        terminal = mac_terminal()
        for phase in ("ram_idle", "ram_heavy"):
            del terminal[phase][0]["cpu"]
        text, err = self.run_report("mac", {"waftty": terminal})
        self.assertNotIn("cpu", self.charts())
        self.assertNotIn("## CPU", text)
        self.assertIn("idle CPU for waftty", err)

    def test_a_chart_with_no_data_does_not_survive_from_an_earlier_report(self):
        self.run_report("linux", {"waftty": linux_terminal()})
        terminal = copy.deepcopy(linux_terminal())
        del terminal["startup"]
        text, _ = self.run_report("linux", {"waftty": terminal})
        self.assertNotIn("startup", self.charts())
        self.assertNotIn("startup.png", text)

    def test_empty_samples_count_as_not_measured(self):
        terminal = mac_terminal()
        terminal["ram_idle"] = []
        _, err = self.run_report("mac", {"waftty": terminal})
        self.assertIn("memory for waftty", err)

    def test_absent_or_empty_results_say_how_to_take_them(self):
        missing = self.dir / "absent.json"
        with self.assertRaises(SystemExit) as caught:
            report.main(["mac", "--results", str(missing), "--out", str(self.out)])
        self.assertIn("uv run mac/bench.py run", str(caught.exception))
        self.assertIn("holds no measurements", self.refused("mac", {"_meta": {"platform": "macos"}}))
        broken = self.dir / "results.json"
        broken.write_text("{")
        with self.assertRaises(SystemExit) as caught:
            report.main(["mac", "--results", str(broken), "--out", str(self.out)])
        self.assertIn("not valid JSON", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
