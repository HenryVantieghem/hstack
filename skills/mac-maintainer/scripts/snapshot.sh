#!/bin/sh

set -u
export LC_ALL=C

usage() {
    printf 'Usage: %s [--help]\nRead-only macOS resource snapshot. No process identifiers or names.\n' "${0##*/}"
}

case "${1-}" in
    -h|--help) usage; exit 0 ;;
    '') ;;
    *) usage >&2; exit 2 ;;
esac

if [ "$#" -ne 0 ]; then
    usage >&2
    exit 2
fi

if [ "$(/usr/bin/uname -s)" != Darwin ]; then
    printf 'This snapshot requires macOS.\n' >&2
    exit 1
fi

printf 'macOS health snapshot (read-only)\n'

disk_target=/
if [ -d /System/Volumes/Data ]; then
    disk_target=/System/Volumes/Data
fi

disk=$(/bin/df -Pk "$disk_target" 2>/dev/null | /usr/bin/awk '
    NR == 2 && $4 ~ /^[0-9]+$/ && $5 ~ /^[0-9]+%$/ {
        printf "%.1f GiB available (%s used)", $4 / 1048576, $5
    }
')
printf 'Startup storage: %s\n' "${disk:-unavailable}"

load=$(/usr/sbin/sysctl -n vm.loadavg 2>/dev/null | /usr/bin/awk '
    NF == 5 && $2 ~ /^[0-9.]+$/ && $3 ~ /^[0-9.]+$/ && $4 ~ /^[0-9.]+$/ {
        printf "%s / %s / %s", $2, $3, $4
    }
')
cores=$(/usr/sbin/sysctl -n hw.logicalcpu 2>/dev/null)
printf 'Load (1 / 5 / 15 min): %s; logical CPUs: %s\n' "${load:-unavailable}" "${cores:-unavailable}"

memory=$(/usr/sbin/sysctl -n hw.memsize 2>/dev/null | /usr/bin/awk '
    /^[0-9]+$/ { printf "%.1f GiB", $1 / 1073741824 }
')
free=$(/usr/bin/memory_pressure -Q 2>/dev/null | /usr/bin/awk '
    /^System-wide memory free percentage:/ && $NF ~ /^[0-9]+%$/ { print $NF }
')
swap=$(/usr/sbin/sysctl -n vm.swapusage 2>/dev/null | /usr/bin/awk '
    $4 == "used" && $6 ~ /^[0-9.]+[KMGT]$/ { print $6 }
')
printf 'Physical RAM: %s\n' "${memory:-unavailable}"
printf 'System-wide memory free estimate: %s\n' "${free:-unavailable}"
printf 'Swap used (macOS units): %s\n' "${swap:-unavailable}"

# Discard the initial top reading and print only the interval sample.
cpu=$(/usr/bin/top -l 2 -s 1 -n 0 2>/dev/null | /usr/bin/awk '
    /^CPU usage:/ && ++samples == 2 && $3 ~ /^[0-9.]+%$/ && $5 ~ /^[0-9.]+%$/ && $7 ~ /^[0-9.]+%$/ {
        printf "%s user, %s system, %s idle", $3, $5, $7
    }
')
printf 'CPU sample: %s\n' "${cpu:-unavailable}"

# Request numeric fields only. Each list is independently ranked.
process_stats=$(/bin/ps -A -o '%cpu=,rss=' 2>/dev/null)
top_cpu=$(printf '%s\n' "$process_stats" | /usr/bin/awk '$1 ~ /^[0-9.]+$/ { print $1 }' |
    /usr/bin/sort -nr | /usr/bin/awk 'NR <= 3 { printf "%s%s%%", (NR == 1 ? "" : ", "), $1 }')
top_rss=$(printf '%s\n' "$process_stats" | /usr/bin/awk '$2 ~ /^[0-9]+$/ { print $2 }' |
    /usr/bin/sort -nr | /usr/bin/awk 'NR <= 3 { printf "%s%.0f MiB", (NR == 1 ? "" : ", "), $1 / 1024 }')
printf 'Top process CPU estimates: %s\n' "${top_cpu:-unavailable}"
printf 'Top process resident memory: %s\n' "${top_rss:-unavailable}"
