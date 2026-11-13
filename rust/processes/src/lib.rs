//! The processes waftty runs, for its Processes view and status bar: a
//! process tree with each process's counters, and signals to its members.

mod sampler;

use gossamer_binding::{GosError, gos_module};

#[gos_module("waftty_processes")]
mod bindings {
    use super::*;

    /// Process `root` and every process descended from it as JSON,
    /// `{"processes": [...]}`, `root` first and each ahead of its children:
    /// pid, parent, name, cpu_ns, memory, disk_read and disk_written.
    pub fn tree(root: i64) -> String {
        let root = u32::try_from(root).unwrap_or(0);
        serde_json::json!({ "processes": sampler::tree(root) }).to_string()
    }

    /// Sends signal `signum` to process `pid`; on Windows, ends it.
    pub fn signal(pid: i64, signum: i64) -> Result<(), GosError> {
        let pid =
            u32::try_from(pid).map_err(|_| GosError::from(format!("{pid} is not a process id")))?;
        let signum = i32::try_from(signum)
            .map_err(|_| GosError::from(format!("{signum} is not a signal")))?;
        Ok(sampler::signal(pid, signum)?)
    }
}
