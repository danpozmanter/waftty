// One process and every process descended from it, with the counters a task
// view samples (CPU time, resident memory, storage I/O), and a signal to any
// of them. Counters are totals so far; a caller samples twice and divides the
// change by the time between to show rates.

use std::io;

use serde::Serialize;

/// One process and its counters at the moment it was sampled.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ProcessSample {
    pub pid: u32,
    /// The process that started it, 0 when the system names none.
    pub parent: u32,
    /// Its program's name, as the system gives it.
    pub name: String,
    /// CPU time it has used, user and system together, in nanoseconds.
    pub cpu_ns: u64,
    /// Resident memory in bytes.
    pub memory: u64,
    /// Bytes it has read from and written to storage, where the system counts
    /// them per process. Windows counts every read and write, devices and
    /// pipes included.
    pub disk_read: Option<u64>,
    pub disk_written: Option<u64>,
}

/// Process `root` and every process descended from it, `root` first and each
/// process ahead of its children; empty when `root` is not running.
pub fn tree(root: u32) -> Vec<ProcessSample> {
    platform::tree(root)
}

/// Sends signal `signum` to process `pid`. Windows has no signals: any signal
/// ends the process there.
pub fn signal(pid: u32, signum: i32) -> io::Result<()> {
    platform::signal(pid, signum)
}

// The processes descended from `root`, given each process's parent, `root`
// first and each ahead of its children.
#[cfg(any(target_os = "linux", target_os = "freebsd", test))]
fn descendants(root: u32, parents: &[(u32, u32)]) -> Vec<u32> {
    use std::collections::{HashMap, HashSet, VecDeque};

    let mut children: HashMap<u32, Vec<u32>> = HashMap::new();
    let mut known = HashSet::new();
    for &(pid, parent) in parents {
        known.insert(pid);
        if pid != parent {
            children.entry(parent).or_default().push(pid);
        }
    }
    if !known.contains(&root) {
        return Vec::new();
    }
    let mut out = Vec::new();
    let mut seen = HashSet::new();
    let mut queue = VecDeque::from([root]);
    while let Some(pid) = queue.pop_front() {
        if !seen.insert(pid) {
            continue;
        }
        out.push(pid);
        if let Some(kids) = children.get(&pid) {
            let mut kids = kids.clone();
            kids.sort_unstable();
            queue.extend(kids);
        }
    }
    out
}

#[cfg(target_os = "linux")]
mod platform {
    use std::collections::HashMap;
    use std::fs;
    use std::io;

    use super::{ProcessSample, descendants};

    pub fn tree(root: u32) -> Vec<ProcessSample> {
        // SAFETY: sysconf reads configuration values and has no preconditions.
        let ticks = unsafe { libc::sysconf(libc::_SC_CLK_TCK) }.max(1) as u64;
        // SAFETY: as above.
        let page = unsafe { libc::sysconf(libc::_SC_PAGESIZE) }.max(1) as u64;
        let mut stats = match subtree(root) {
            Some(stats) => stats,
            None => everything(),
        };
        let parents: Vec<(u32, u32)> = stats.iter().map(|(&pid, s)| (pid, s.parent)).collect();
        descendants(root, &parents)
            .into_iter()
            .filter_map(|pid| {
                let s = stats.remove(&pid)?;
                let (disk_read, disk_written) = io_bytes(pid);
                Some(ProcessSample {
                    pid,
                    parent: s.parent,
                    name: s.name,
                    cpu_ns: s.cpu_ticks.saturating_mul(1_000_000_000) / ticks,
                    memory: s.rss_pages.saturating_mul(page),
                    disk_read,
                    disk_written,
                })
            })
            .collect()
    }

    // The records of `root` and its descendants, found through each
    // thread's `children` file, which reads only the processes in the tree;
    // None where the kernel keeps no such file.
    pub(super) fn subtree(root: u32) -> Option<HashMap<u32, Stat>> {
        let mut stats = HashMap::new();
        let Some(first) = stat(root) else {
            return Some(stats);
        };
        stats.insert(root, first);
        let mut queue = vec![root];
        while let Some(pid) = queue.pop() {
            // Each thread lists the children it started.
            let Ok(threads) = fs::read_dir(format!("/proc/{pid}/task")) else {
                continue;
            };
            for thread in threads.flatten() {
                let file = thread.path().join("children");
                let text = match fs::read_to_string(&file) {
                    Ok(text) => text,
                    Err(e) if e.kind() == io::ErrorKind::NotFound && pid == root => return None,
                    Err(_) => continue,
                };
                for child in text
                    .split_whitespace()
                    .filter_map(|c| c.parse::<u32>().ok())
                {
                    if !stats.contains_key(&child)
                        && let Some(s) = stat(child)
                    {
                        stats.insert(child, s);
                        queue.push(child);
                    }
                }
            }
        }
        Some(stats)
    }

    // Every process's record, for kernels without `children` files.
    pub(super) fn everything() -> HashMap<u32, Stat> {
        let Ok(entries) = fs::read_dir("/proc") else {
            return HashMap::new();
        };
        entries
            .flatten()
            .filter_map(|e| e.file_name().to_str().and_then(|n| n.parse::<u32>().ok()))
            .filter_map(|pid| Some((pid, stat(pid)?)))
            .collect()
    }

    // A process that ended since it was listed has no record left.
    fn stat(pid: u32) -> Option<Stat> {
        parse_stat(&fs::read_to_string(format!("/proc/{pid}/stat")).ok()?)
    }

    /// What `/proc/<pid>/stat` says of a process.
    #[derive(Debug, PartialEq, Eq)]
    pub(super) struct Stat {
        pub name: String,
        pub parent: u32,
        pub cpu_ticks: u64,
        pub rss_pages: u64,
    }

    // The program name sits in parentheses and may hold spaces or
    // parentheses itself, so the fields after it are counted from its last
    // closing parenthesis.
    pub(super) fn parse_stat(text: &str) -> Option<Stat> {
        let open = text.find('(')?;
        let close = text.rfind(')')?;
        let name = text.get(open + 1..close)?.to_string();
        let fields: Vec<&str> = text.get(close + 1..)?.split_whitespace().collect();
        let field = |i: usize| fields.get(i).and_then(|f| f.parse::<u64>().ok());
        // After the name: state, ppid, ... utime (11), stime (12), ... rss (21).
        Some(Stat {
            name,
            parent: field(1)? as u32,
            cpu_ticks: field(11)? + field(12)?,
            rss_pages: field(21)?,
        })
    }

    // Storage bytes from `/proc/<pid>/io`, which only the process's own user
    // (or root) may read.
    fn io_bytes(pid: u32) -> (Option<u64>, Option<u64>) {
        let Ok(text) = fs::read_to_string(format!("/proc/{pid}/io")) else {
            return (None, None);
        };
        let value = |key: &str| {
            text.lines()
                .find_map(|l| l.strip_prefix(key))
                .and_then(|v| v.trim().parse::<u64>().ok())
        };
        (value("read_bytes:"), value("write_bytes:"))
    }

    pub fn signal(pid: u32, signum: i32) -> io::Result<()> {
        // SAFETY: kill takes plain integers; a wrong pid or signal is an error
        // it reports, not undefined behavior.
        if unsafe { libc::kill(pid as libc::pid_t, signum) } == 0 {
            Ok(())
        } else {
            Err(io::Error::last_os_error())
        }
    }
}

#[cfg(target_os = "macos")]
mod platform {
    use std::io;

    use super::ProcessSample;

    // libproc.h: list only the processes whose parent is the one given.
    const PROC_PPID_ONLY: u32 = 6;

    // How Mach absolute time converts to nanoseconds: multiply by `numer`,
    // divide by `denom` (mach/mach_time.h).
    #[repr(C)]
    #[derive(Clone, Copy)]
    struct Timebase {
        numer: u32,
        denom: u32,
    }

    unsafe extern "C" {
        fn mach_timebase_info(info: *mut Timebase) -> libc::c_int;
    }

    pub fn tree(root: u32) -> Vec<ProcessSample> {
        let mut timebase = Timebase { numer: 1, denom: 1 };
        // SAFETY: `timebase` is a writable record the call fills.
        unsafe { mach_timebase_info(&raw mut timebase) };
        let mut out = Vec::new();
        let Some(first) = sample(root, 0, timebase) else {
            return out;
        };
        out.push(first);
        let mut next = 0;
        while next < out.len() {
            let parent = out[next].pid;
            for pid in children(parent) {
                if out.iter().all(|s| s.pid != pid)
                    && let Some(s) = sample(pid, parent, timebase)
                {
                    out.push(s);
                }
            }
            next += 1;
        }
        out
    }

    fn children(parent: u32) -> Vec<u32> {
        let mut pids = vec![0 as libc::c_int; 256];
        loop {
            let size = (pids.len() * std::mem::size_of::<libc::c_int>()) as libc::c_int;
            // SAFETY: `pids` is writable storage of `size` bytes.
            let bytes = unsafe {
                libc::proc_listpids(PROC_PPID_ONLY, parent, pids.as_mut_ptr().cast(), size)
            };
            if bytes <= 0 {
                return Vec::new();
            }
            // A full buffer may have been cut short: list again in a larger one.
            if bytes >= size {
                pids.resize(pids.len() * 2, 0);
                continue;
            }
            let count = bytes as usize / std::mem::size_of::<libc::c_int>();
            return pids[..count]
                .iter()
                .filter(|&&p| p > 0)
                .map(|&p| p as u32)
                .collect();
        }
    }

    fn sample(pid: u32, parent: u32, timebase: Timebase) -> Option<ProcessSample> {
        // SAFETY: the record is plain old data, which all zeros initializes.
        let mut usage: libc::rusage_info_v2 = unsafe { std::mem::zeroed() };
        // SAFETY: `usage` is a writable rusage_info_v2, the flavor asked for.
        let read = unsafe {
            libc::proc_pid_rusage(
                pid as libc::c_int,
                libc::RUSAGE_INFO_V2,
                (&raw mut usage).cast(),
            )
        };
        if read != 0 {
            return None;
        }
        // CPU times count Mach absolute time units, nanoseconds only on Intel.
        let ticks = usage.ri_user_time.saturating_add(usage.ri_system_time) as u128;
        let cpu_ns = (ticks * timebase.numer as u128 / timebase.denom.max(1) as u128) as u64;
        let mut name = [0u8; 256];
        // SAFETY: `name` is writable storage of the length given.
        let len = unsafe {
            libc::proc_name(
                pid as libc::c_int,
                name.as_mut_ptr().cast(),
                name.len() as u32,
            )
        };
        let name = if len > 0 {
            String::from_utf8_lossy(&name[..len as usize]).into_owned()
        } else {
            String::new()
        };
        Some(ProcessSample {
            pid,
            parent,
            name,
            cpu_ns,
            memory: usage.ri_resident_size,
            disk_read: Some(usage.ri_diskio_bytesread),
            disk_written: Some(usage.ri_diskio_byteswritten),
        })
    }

    pub fn signal(pid: u32, signum: i32) -> io::Result<()> {
        // SAFETY: kill takes plain integers; a wrong pid or signal is an error
        // it reports, not undefined behavior.
        if unsafe { libc::kill(pid as libc::pid_t, signum) } == 0 {
            Ok(())
        } else {
            Err(io::Error::last_os_error())
        }
    }
}

#[cfg(target_os = "freebsd")]
mod platform {
    use std::collections::HashMap;
    use std::io;

    use super::{ProcessSample, descendants};

    pub fn tree(root: u32) -> Vec<ProcessSample> {
        // SAFETY: sysconf reads configuration values and has no preconditions.
        let page = unsafe { libc::sysconf(libc::_SC_PAGESIZE) }.max(1) as u64;
        let records = all();
        let parents: Vec<(u32, u32)> = records
            .iter()
            .map(|k| (k.ki_pid as u32, k.ki_ppid as u32))
            .collect();
        let by_pid: HashMap<u32, &libc::kinfo_proc> =
            records.iter().map(|k| (k.ki_pid as u32, k)).collect();
        descendants(root, &parents)
            .into_iter()
            .filter_map(|pid| {
                let k = by_pid.get(&pid)?;
                // SAFETY: the kernel writes a NUL-terminated name into ki_comm.
                let name = unsafe { std::ffi::CStr::from_ptr(k.ki_comm.as_ptr()) };
                // FreeBSD counts storage operations per process, not bytes.
                Some(ProcessSample {
                    pid,
                    parent: k.ki_ppid as u32,
                    name: name.to_string_lossy().into_owned(),
                    cpu_ns: k.ki_runtime.saturating_mul(1_000),
                    memory: (k.ki_rssize.max(0) as u64).saturating_mul(page),
                    disk_read: None,
                    disk_written: None,
                })
            })
            .collect()
    }

    // Every process's record, from `kern.proc.proc`.
    fn all() -> Vec<libc::kinfo_proc> {
        let mut mib = [libc::CTL_KERN, libc::KERN_PROC, libc::KERN_PROC_PROC, 0];
        let record = std::mem::size_of::<libc::kinfo_proc>();
        for _ in 0..4 {
            let mut len = 0usize;
            // SAFETY: a null buffer asks only for the size the records need.
            if unsafe {
                libc::sysctl(
                    mib.as_mut_ptr(),
                    4,
                    std::ptr::null_mut(),
                    &raw mut len,
                    std::ptr::null(),
                    0,
                )
            } != 0
            {
                return Vec::new();
            }
            // Room for processes started between the two calls.
            let mut records: Vec<libc::kinfo_proc> = Vec::with_capacity(len / record + 16);
            let mut len = records.capacity() * record;
            // SAFETY: `records` has room for `len` bytes of records.
            let done = unsafe {
                libc::sysctl(
                    mib.as_mut_ptr(),
                    4,
                    records.as_mut_ptr().cast(),
                    &raw mut len,
                    std::ptr::null(),
                    0,
                )
            };
            if done == 0 {
                // SAFETY: the kernel wrote `len` bytes of whole records.
                unsafe { records.set_len(len / record) };
                return records
                    .into_iter()
                    .filter(|k| k.ki_structsize as usize == record)
                    .collect();
            }
            if io::Error::last_os_error().raw_os_error() != Some(libc::ENOMEM) {
                return Vec::new();
            }
        }
        Vec::new()
    }

    pub fn signal(pid: u32, signum: i32) -> io::Result<()> {
        // SAFETY: kill takes plain integers; a wrong pid or signal is an error
        // it reports, not undefined behavior.
        if unsafe { libc::kill(pid as libc::pid_t, signum) } == 0 {
            Ok(())
        } else {
            Err(io::Error::last_os_error())
        }
    }
}

#[cfg(windows)]
mod platform {
    use std::collections::HashMap;
    use std::io;

    use windows_sys::Win32::Foundation::{CloseHandle, FILETIME, HANDLE, INVALID_HANDLE_VALUE};
    use windows_sys::Win32::System::Diagnostics::ToolHelp::{
        CreateToolhelp32Snapshot, PROCESSENTRY32W, Process32FirstW, Process32NextW,
        TH32CS_SNAPPROCESS,
    };
    use windows_sys::Win32::System::ProcessStatus::{
        K32GetProcessMemoryInfo, PROCESS_MEMORY_COUNTERS,
    };
    use windows_sys::Win32::System::Threading::{
        GetProcessIoCounters, GetProcessTimes, IO_COUNTERS, OpenProcess,
        PROCESS_QUERY_LIMITED_INFORMATION, PROCESS_TERMINATE, TerminateProcess,
    };

    use super::ProcessSample;

    // An open process handle, closed when dropped.
    struct Process(HANDLE);

    impl Process {
        fn open(pid: u32, access: u32) -> Option<Process> {
            // SAFETY: OpenProcess takes plain values and answers null on failure.
            let handle = unsafe { OpenProcess(access, 0, pid) };
            (!handle.is_null()).then_some(Process(handle))
        }

        // When it started and the CPU time it has used, both in 100 ns units.
        fn times(&self) -> Option<(u64, u64)> {
            let zero = FILETIME {
                dwLowDateTime: 0,
                dwHighDateTime: 0,
            };
            let (mut created, mut exited, mut kernel, mut user) = (zero, zero, zero, zero);
            // SAFETY: the handle is open with query access and each FILETIME is writable.
            let ok = unsafe {
                GetProcessTimes(
                    self.0,
                    &raw mut created,
                    &raw mut exited,
                    &raw mut kernel,
                    &raw mut user,
                )
            };
            (ok != 0).then(|| (ticks(created), ticks(kernel) + ticks(user)))
        }
    }

    impl Drop for Process {
        fn drop(&mut self) {
            // SAFETY: the handle came from OpenProcess and is closed once.
            unsafe { CloseHandle(self.0) };
        }
    }

    fn ticks(t: FILETIME) -> u64 {
        ((t.dwHighDateTime as u64) << 32) | t.dwLowDateTime as u64
    }

    pub fn tree(root: u32) -> Vec<ProcessSample> {
        let listed = all();
        let mut children: HashMap<u32, Vec<(u32, String)>> = HashMap::new();
        let mut names = HashMap::new();
        for (pid, parent, name) in listed {
            names.insert(pid, name.clone());
            if pid != parent {
                children.entry(parent).or_default().push((pid, name));
            }
        }
        let Some(name) = names.remove(&root) else {
            return Vec::new();
        };
        let Some(first) = sample(root, 0, name) else {
            return Vec::new();
        };
        let mut out = vec![first];
        let mut started = vec![0u64];
        let mut next = 0;
        while next < out.len() {
            let parent = out[next].pid;
            let parent_started = started[next];
            for (pid, name) in children.get(&parent).cloned().unwrap_or_default() {
                // Windows keeps a parent's id after it exits, and may give it
                // to a later process: a child began after its parent did.
                let Some(child) = Process::open(pid, PROCESS_QUERY_LIMITED_INFORMATION) else {
                    continue;
                };
                let Some((began, _)) = child.times() else {
                    continue;
                };
                if began < parent_started || out.iter().any(|s| s.pid == pid) {
                    continue;
                }
                if let Some(s) = sample(pid, parent, name) {
                    out.push(s);
                    started.push(began);
                }
            }
            next += 1;
        }
        out
    }

    // Every process's id, parent and program, from a Toolhelp snapshot.
    fn all() -> Vec<(u32, u32, String)> {
        // SAFETY: the snapshot call takes plain values.
        let snapshot = unsafe { CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0) };
        if snapshot == INVALID_HANDLE_VALUE {
            return Vec::new();
        }
        let snapshot = Process(snapshot);
        let mut out = Vec::new();
        // SAFETY: the record is plain old data, which all zeros initializes.
        let mut entry: PROCESSENTRY32W = unsafe { std::mem::zeroed() };
        entry.dwSize = std::mem::size_of::<PROCESSENTRY32W>() as u32;
        // SAFETY: `entry` is a writable record whose dwSize is set.
        let mut more = unsafe { Process32FirstW(snapshot.0, &raw mut entry) } != 0;
        while more {
            let len = entry
                .szExeFile
                .iter()
                .position(|&c| c == 0)
                .unwrap_or(entry.szExeFile.len());
            out.push((
                entry.th32ProcessID,
                entry.th32ParentProcessID,
                String::from_utf16_lossy(&entry.szExeFile[..len]),
            ));
            // SAFETY: as above.
            more = unsafe { Process32NextW(snapshot.0, &raw mut entry) } != 0;
        }
        out
    }

    fn sample(pid: u32, parent: u32, name: String) -> Option<ProcessSample> {
        let process = Process::open(pid, PROCESS_QUERY_LIMITED_INFORMATION)?;
        let (_, cpu) = process.times()?;
        // SAFETY: the record is plain old data, which all zeros initializes.
        let mut memory: PROCESS_MEMORY_COUNTERS = unsafe { std::mem::zeroed() };
        let size = std::mem::size_of::<PROCESS_MEMORY_COUNTERS>() as u32;
        // SAFETY: the handle is open with query access and `memory` holds `size` bytes.
        let memory = if unsafe { K32GetProcessMemoryInfo(process.0, &raw mut memory, size) } != 0 {
            memory.WorkingSetSize as u64
        } else {
            0
        };
        // SAFETY: the record is plain old data, which all zeros initializes.
        let mut counters: IO_COUNTERS = unsafe { std::mem::zeroed() };
        // SAFETY: the handle is open with query access and `counters` is writable.
        let io = unsafe { GetProcessIoCounters(process.0, &raw mut counters) } != 0;
        Some(ProcessSample {
            pid,
            parent,
            name,
            cpu_ns: cpu.saturating_mul(100),
            memory,
            disk_read: io.then_some(counters.ReadTransferCount),
            disk_written: io.then_some(counters.WriteTransferCount),
        })
    }

    pub fn signal(pid: u32, _signum: i32) -> io::Result<()> {
        let process = Process::open(pid, PROCESS_TERMINATE).ok_or_else(io::Error::last_os_error)?;
        // SAFETY: the handle is open with terminate access.
        if unsafe { TerminateProcess(process.0, 1) } != 0 {
            Ok(())
        } else {
            Err(io::Error::last_os_error())
        }
    }
}

#[cfg(not(any(
    target_os = "linux",
    target_os = "macos",
    target_os = "freebsd",
    windows
)))]
mod platform {
    use std::io;

    use super::ProcessSample;

    pub fn tree(_root: u32) -> Vec<ProcessSample> {
        Vec::new()
    }

    pub fn signal(_pid: u32, _signum: i32) -> io::Result<()> {
        Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "this system lists no processes",
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Tests that start children share this process's tree, so they run one
    // at a time.
    static CHILDREN: std::sync::Mutex<()> = std::sync::Mutex::new(());

    #[test]
    fn descendants_lists_the_root_then_each_generation_and_skips_strangers() {
        let parents = [
            (1, 0),
            (10, 1),
            (11, 10),
            (12, 10),
            (13, 11),
            (20, 1),
            (99, 98),
        ];
        assert_eq!(descendants(10, &parents), vec![10, 11, 12, 13]);
        assert_eq!(descendants(98, &parents), Vec::<u32>::new());
        assert_eq!(descendants(99, &parents), vec![99]);
    }

    #[test]
    fn descendants_survives_a_process_listed_as_its_own_parent() {
        assert_eq!(descendants(0, &[(0, 0), (1, 0)]), vec![0, 1]);
    }

    #[cfg(target_os = "linux")]
    #[test]
    fn a_stat_line_reads_past_a_name_with_spaces_and_parentheses() {
        let line = "4242 (my (odd) prog) S 4200 4242 4200 34816 4242 4194304 120 0 0 0 7 3 0 0 20 0 1 0 900 10485760 512 18446744073709551615";
        let stat = platform::parse_stat(line).expect("a stat line");
        assert_eq!(
            stat,
            platform::Stat {
                name: "my (odd) prog".into(),
                parent: 4200,
                cpu_ticks: 10,
                rss_pages: 512
            }
        );
    }

    #[cfg(target_os = "linux")]
    #[test]
    fn the_subtree_walk_finds_what_a_scan_of_every_process_finds() {
        let _one = CHILDREN.lock().unwrap_or_else(|e| e.into_inner());
        let mut child = std::process::Command::new("sleep")
            .arg("30")
            .spawn()
            .expect("sleep runs");
        let me = std::process::id();
        let walked = platform::subtree(me).expect("this kernel keeps children files");
        let all = platform::everything();
        let parents: Vec<(u32, u32)> = all.iter().map(|(&pid, s)| (pid, s.parent)).collect();
        let mut scanned = descendants(me, &parents);
        let mut found: Vec<u32> = walked.keys().copied().collect();
        scanned.sort_unstable();
        found.sort_unstable();
        assert_eq!(found, scanned);
        assert!(found.contains(&child.id()));
        child.kill().expect("sleep ends");
        child.wait().expect("sleep is reaped");
    }

    #[cfg(any(
        target_os = "linux",
        target_os = "macos",
        target_os = "freebsd",
        windows
    ))]
    #[test]
    fn the_tree_holds_this_process_and_a_child_it_started_until_a_signal_ends_it() {
        let _one = CHILDREN.lock().unwrap_or_else(|e| e.into_inner());
        #[cfg(unix)]
        let mut child = std::process::Command::new("sleep")
            .arg("30")
            .spawn()
            .expect("sleep runs");
        #[cfg(windows)]
        let mut child = std::process::Command::new("cmd")
            .args(["/C", "ping -n 30 127.0.0.1 >NUL"])
            .spawn()
            .expect("ping runs");
        let me = std::process::id();
        let found = tree(me);
        assert_eq!(found.first().map(|s| s.pid), Some(me));
        assert!(found[0].memory > 0, "{:?}", found[0]);
        let kid = found
            .iter()
            .find(|s| s.pid == child.id())
            .expect("the child is listed");
        assert_eq!(kid.parent, me);
        assert!(!kid.name.is_empty());
        #[cfg(unix)]
        signal(child.id(), libc::SIGTERM).expect("the signal is sent");
        #[cfg(windows)]
        signal(child.id(), 15).expect("the process ends");
        child.wait().expect("the child is reaped");
        assert!(tree(me).iter().all(|s| s.pid != child.id()));
    }
}
