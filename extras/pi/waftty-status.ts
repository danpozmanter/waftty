/**
 * Tells the terminal what pi is doing, by the Program Status Protocol (OSC
 * 7501), so a terminal such as waftty alerts when pi waits for you: whenever
 * an extension asks you something, such as a permission or a choice. pi
 * ending its turn is not an alert.
 *
 * Install: copy this file to ~/.pi/agent/extensions/.
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

const WRAPPED = Symbol.for("waftty-status");

// One line of at most 200 characters, without control characters.
function line(text: unknown): string {
	return String(text ?? "").replace(/[\u0000-\u001f\u007f-\u009f]+/g, " ").replace(/\s+/g, " ").trim().slice(0, 200);
}

function report(state: string, kind = "", msg = ""): void {
	const text = line(msg);
	let pairs = `state=${state}:app=pi`;
	if (kind) pairs += `:kind=${kind}`;
	if (text) pairs += `:msg=${Buffer.from(text).toString("base64")}`;
	process.stdout.write(`\x1b]7501;${pairs}\x1b\\`);
}

export default function (pi: ExtensionAPI) {
	let working = false;
	pi.on("agent_start", async () => {
		working = true;
		report("working");
	});
	pi.on("agent_end", async () => {
		working = false;
		report("idle");
	});
	// Every extension shares pi's one UI, so each question it asks passes here.
	pi.on("session_start", async (_event, ctx) => {
		const ui = ctx.ui as any;
		if (ui[WRAPPED]) return;
		ui[WRAPPED] = true;
		for (const name of ["select", "confirm", "input", "editor"]) {
			const ask = ui[name]?.bind(ui);
			if (!ask) continue;
			ui[name] = async (...args: unknown[]) => {
				report("blocked", "question", String(args[0] ?? ""));
				try {
					return await ask(...args);
				} finally {
					report(working ? "working" : "idle");
				}
			};
		}
	});
	pi.on("session_shutdown", async () => report("clear"));
}
