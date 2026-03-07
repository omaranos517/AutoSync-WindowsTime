#define MyAppName "TimeSync"
#define MyAppVersion "1.2.0"
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
OutputDir={#SourcePath}\..\output
OutputBaseFilename=TimeSync_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern dynamic

[Files]
Source: "{#SourcePath}\..\dist\TimeSync\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Tasks]
Name: "startup"; Description: "Run TimeSync at Windows startup"; Flags: checkedonce

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "startup enable"; Tasks: startup; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Parameters: "resume enable"; Tasks: startup; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "Launch TimeSync"; Flags: nowait postinstall skipifsilent

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; AppUserModelID: "{#MyAppUserModelID}"

[Code]
// --- تعريف وظائف الويندوز لحل مشكلة Unknown identifier ---
#ifdef UNICODE
  #define AW "W"
#else
  #define AW "A"
#endif

type
  WPARAM = UINT_PTR;
  LPARAM = INT_PTR;

function SendMessageTimeout(hWnd: HWND; Msg: UINT; wParam: WPARAM; lParam: PAnsiChar; fuFlags: UINT; uTimeout: UINT; var lpdwResult: DWORD): Longint;
  external 'SendMessageTimeout{#AW}@user32.dll stdcall';

const
  WM_SETTINGCHANGE = $001A;
  SMTO_ABORTIFHUNG = $0002;

procedure AddToPath();
var
  OldPath: string;
  NewPath: string;
  ResultCode: DWORD;
begin
  // جلب المسار الحالي من الريجستري
  if RegQueryStringValue(HKEY_LOCAL_MACHINE,
     'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
     'Path', OldPath) then
  begin
    // التحقق مما إذا كان المسار موجوداً مسبقاً (تجاهل حالة الأحرف)
    if Pos(Uppercase(ExpandConstant('{app}')), Uppercase(OldPath)) = 0 then
    begin
      NewPath := OldPath;
      if (Length(NewPath) > 0) and (NewPath[Length(NewPath)] <> ';') then
        NewPath := NewPath + ';';
      
      NewPath := NewPath + ExpandConstant('{app}');

      // كتابة المسار الجديد
      if RegWriteStringValue(HKEY_LOCAL_MACHINE,
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
        'Path', NewPath) then
      begin
        // إبلاغ النظام بتحديث المتغيرات
        SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 5000, ResultCode);
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    AddToPath();
    MsgBox('✅ Successfully installed' + #13#10 + '🚀 You can now use timesync in any Terminal.', mbInformation, MB_OK);
  end;
end;
