tell application "Terminal"
    do script "cd \"" & POSIX path of (path to me as text) & "\" && ./launch_dashboard.sh"
    activate
end tell 