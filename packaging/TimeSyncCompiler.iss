#define MyAppName "TimeSync"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Omar Anoss"
#define MyAppExeName "timesync-gui.exe"
#define MyAppUserModelID "OmarAnoss.TimeSync"

[Setup]
AppId={{F1A0C0F3-1234-4EAA-9999-ABCDE1234567}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppSupportURL=https://github.com/omaranos517/AutoSync-WindowsTime
SetupIconFile={#SourcePath}\..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64
DefaultDirName={autopf}\TimeSync
DefaultGroupName=TimeSync
ChangesEnvironment=yes
OutputDir={#SourcePath}\..\output
OutputBaseFilename=TimeSync_v{#MyAppVersion}_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern dynamic

[Files]
Source: "{#SourcePath}\..\dist\TimeSync\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Tasks]
Name: "startup"; Description: "Run TimeSync at Windows startup"; Flags: checkedonce

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "startup enable"; Tasks: startup; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Parameters: "resume enable"; Tasks: startup; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Parameters: "completion powershell --install"; Flags: runhidden runasoriginaluser waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Launch TimeSync"; Flags: nowait postinstall skipifsilent

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; AppUserModelID: "{#MyAppUserModelID}"

[Code]
#ifdef UNICODE
  #define AW "W"
#else
  #define AW "A"
#endif

type
  WPARAM = UINT_PTR;
  LPARAM = INT_PTR;

function SendMessageTimeout(hWnd: HWND; Msg: UINT; wParam: WPARAM; lParam: String; fuFlags: UINT; uTimeout: UINT; var lpdwResult: DWORD): Longint;
  external 'SendMessageTimeout{#AW}@user32.dll stdcall';

const
  WM_SETTINGCHANGE = $001A;
  SMTO_ABORTIFHUNG = $0002;

var
  DeleteUserDataOnUninstall: Boolean;

function GetUserDataDir(): string;
begin
  Result := ExpandConstant('{localappdata}\{#MyAppName}');
end;

procedure AddToPath();
var
  OldPath, NewPath: string;
  ResultCode: DWORD;
  AppPath: string;
begin
  AppPath := ExpandConstant('{app}');
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', OldPath) then
  begin
    if Pos(';' + Uppercase(AppPath) + ';', ';' + Uppercase(OldPath) + ';') = 0 then
    begin
      NewPath := OldPath;
      if (Length(NewPath) > 0) and (NewPath[Length(NewPath)] <> ';') then
        NewPath := NewPath + ';';
      
      NewPath := NewPath + AppPath;

      if RegWriteStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', NewPath) then
      begin
        SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 5000, ResultCode);
      end;
    end;
  end;
end;


procedure RemoveFromPath();
var
  OldPath, NewPath: string;
  AppPath: string;
  P: Integer;
  ResultCode: DWORD;
begin
  AppPath := ExpandConstant('{app}');
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', OldPath) then
  begin
    P := Pos(';' + Uppercase(AppPath), ';' + Uppercase(OldPath));
    if P > 0 then
    begin
      NewPath := OldPath;
      StringChangeEx(NewPath, AppPath + ';', '', True);
      StringChangeEx(NewPath, AppPath, '', True);
      
      StringChangeEx(NewPath, ';;', ';', True);

      if RegWriteStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', NewPath) then
      begin
        SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 5000, ResultCode);
      end;
    end;
  end;
end;

procedure InitializeWizard();
begin
  if RegKeyExists(HKEY_LOCAL_MACHINE,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\TimeSync') then
  begin
    RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE,
      'Software\Microsoft\Windows\CurrentVersion\Uninstall\TimeSync');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    AddToPath();
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    RemoveFromPath();
    DeleteUserDataOnUninstall := False;

    if DirExists(GetUserDataDir()) then
    begin
      if MsgBox(
        'Do you want to delete settings and log files?' + #13#10 +
        '(This will remove your history and preferences)',
        mbConfirmation,
        MB_YESNO
      ) = IDYES then
      begin
        DeleteUserDataOnUninstall := True;
      end;
    end;
  end;

  if CurUninstallStep = usPostUninstall then
  begin
    if DeleteUserDataOnUninstall and DirExists(GetUserDataDir()) then
    begin
      DelTree(GetUserDataDir(), True, True, True);
    end;
  end;
end;
