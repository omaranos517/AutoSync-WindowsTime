$TimeSyncTopLevel = @(__TOP_LEVEL_COMMANDS__)
$TimeSyncActions = @{
__ACTION_MAP__
}

Register-ArgumentCompleter -Native -CommandName 'timesync', 'timesync.bat', 'timesync-cli.exe' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    function Complete-TimeSyncValues {
        param(
            [string[]]$Values,
            [string]$CompletionType = 'ParameterValue'
        )

        $Values | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, $CompletionType, $_)
        }
    }

    $tokens = @($commandAst.CommandElements | Select-Object -Skip 1 | ForEach-Object {
        $_.Extent.Text -replace "^[`"'']+|[`"'']+$", ''
    })

    if ($tokens.Count -eq 0) {
        Complete-TimeSyncValues -Values $TimeSyncTopLevel
        return
    }

    $command = $tokens[0]
    $knownTopLevel = $TimeSyncTopLevel -contains $command

    if ($tokens.Count -eq 1) {
        if (-not $knownTopLevel) {
            Complete-TimeSyncValues -Values $TimeSyncTopLevel
            return
        }

        if ($command -eq 'now') {
            Complete-TimeSyncValues -Values @('--auto') -CompletionType 'ParameterName'
            return
        }

        if ($TimeSyncActions.ContainsKey($command)) {
            Complete-TimeSyncValues -Values $TimeSyncActions[$command]
            return
        }

        if ($command -eq 'completion') {
            Complete-TimeSyncValues -Values @('powershell')
        }
        return
    }

    if ($TimeSyncActions.ContainsKey($command) -and $tokens.Count -eq 2) {
        Complete-TimeSyncValues -Values $TimeSyncActions[$command]
        return
    }

    if ($command -eq 'completion' -and $tokens.Count -eq 2) {
        Complete-TimeSyncValues -Values @('--install') -CompletionType 'ParameterName'
        return
    }

    if ($command -eq 'completion' -and $tokens.Count -eq 3 -and $tokens[1] -eq 'powershell') {
        Complete-TimeSyncValues -Values @('--install') -CompletionType 'ParameterName'
        return
    }

    if ($command -eq 'now' -and $tokens.Count -eq 2) {
        Complete-TimeSyncValues -Values @('--auto') -CompletionType 'ParameterName'
    }
}
