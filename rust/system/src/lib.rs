//! What waftty reads from the system: the processes it runs, for its
//! Processes view and status bar, with signals to them, and the local time
//! zone, for the dates it shows.

mod clock;
mod sampler;

use gossamer_binding::{GosError, gos_module};

#[gos_module("waftty_system")]
mod bindings {
    use super::*;

    /// Process `root` and every process descended from it as JSON,
    /// `{"processes": [...]}`, `root` first and each ahead of its children:
    /// pid, parent, name, cpu_ns, memory, disk_read and disk_written.
    pub fn processes(root: i64) -> String {
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

    /// Seconds local time is ahead of UTC at `unix_seconds`, by the
    /// system's zone rules for that moment.
    pub fn local_offset(unix_seconds: i64) -> i64 {
        clock::local_offset(unix_seconds)
    }
}
