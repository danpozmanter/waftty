// The theme keeps the repository's latest release, stars, and forks for the
// whole browser session; dropping them at each page load makes the header
// show GitHub's facts as of this visit.
sessionStorage.removeItem(__md_scope.pathname + ".__source")
