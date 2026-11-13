//! The local time zone as the system keeps it, so waftty shows local dates
//! without carrying a time zone database of its own.

/// Seconds local time is ahead of UTC at `unix_seconds`, by the system's
/// zone rules for that moment; 0 when the system cannot say.
#[cfg(unix)]
pub fn local_offset(unix_seconds: i64) -> i64 {
    // time_t and long are 64 bits wide on every Unix waftty runs on.
    let at: libc::time_t = unix_seconds;
    // POSIX on every Unix waftty runs on; the libc crate does not declare it.
    unsafe extern "C" {
        fn tzset();
    }
    let mut civil = std::mem::MaybeUninit::<libc::tm>::zeroed();
    // SAFETY: tzset only rereads the zone settings, so a zone the system
    // changes to since shows; localtime_r reads `at` and writes the `tm` it
    // is handed, nothing else.
    let filled = unsafe {
        tzset();
        !libc::localtime_r(&at, civil.as_mut_ptr()).is_null()
    };
    if !filled {
        return 0;
    }
    // SAFETY: localtime_r filled `civil`, as its non-null answer says.
    unsafe { civil.assume_init() }.tm_gmtoff
}

/// Seconds local time is ahead of UTC at `unix_seconds`, by the system's
/// zone rules for that moment; 0 when the system cannot say.
#[cfg(windows)]
pub fn local_offset(unix_seconds: i64) -> i64 {
    use windows_sys::Win32::Foundation::{FILETIME, SYSTEMTIME};
    use windows_sys::Win32::System::Time::{
        FileTimeToSystemTime, SystemTimeToFileTime, SystemTimeToTzSpecificLocalTime,
    };

    // FILETIME counts 100 ns ticks from 1601-01-01.
    const UNIX_EPOCH_TICKS: i64 = 116_444_736_000_000_000;
    const TICKS_PER_SECOND: i64 = 10_000_000;
    let Some(ticks) = unix_seconds
        .checked_mul(TICKS_PER_SECOND)
        .and_then(|t| t.checked_add(UNIX_EPOCH_TICKS))
        .filter(|t| *t >= 0)
    else {
        return 0;
    };
    let file_time = |ticks: i64| FILETIME {
        dwLowDateTime: ticks as u32,
        dwHighDateTime: (ticks >> 32) as u32,
    };
    let utc_file = file_time(ticks);
    let mut utc = SYSTEMTIME::default();
    let mut local = SYSTEMTIME::default();
    let mut local_file = file_time(0);
    // SAFETY: each call reads and writes only the structures it is handed;
    // a null zone means the zone the system runs in.
    let converted = unsafe {
        FileTimeToSystemTime(&utc_file, &mut utc) != 0
            && SystemTimeToTzSpecificLocalTime(std::ptr::null(), &utc, &mut local) != 0
            && SystemTimeToFileTime(&local, &mut local_file) != 0
    };
    if !converted {
        return 0;
    }
    let local_ticks =
        (i64::from(local_file.dwHighDateTime) << 32) | i64::from(local_file.dwLowDateTime);
    (local_ticks - ticks) / TICKS_PER_SECOND
}

#[cfg(test)]
mod tests {
    #[test]
    fn the_offset_follows_the_zone_and_its_daylight_saving_rules() {
        let offset = super::local_offset(1_794_594_011);
        assert!(offset.abs() < 86_400);
        assert_eq!(offset % 60, 0);
        #[cfg(unix)]
        {
            // SAFETY: this is the crate's one test that reads or writes TZ,
            // so no other thread touches the environment meanwhile.
            unsafe { std::env::set_var("TZ", "America/New_York") };
            let winter = super::local_offset(1_794_594_011);
            let summer = super::local_offset(1_783_000_000);
            // SAFETY: as above.
            unsafe { std::env::remove_var("TZ") };
            assert_eq!(winter, -5 * 3_600);
            assert_eq!(summer, -4 * 3_600);
        }
    }
}
