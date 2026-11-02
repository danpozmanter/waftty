; The Windows installer. scripts/package.sh --installers compiles it with
; AppVersion, Payload (the folder holding waftty.exe), IconFile and
; LicenseFile defined, and names the output.
#define AppName "waftty"
#define AppExe "waftty.exe"
#define AppUrl "https://github.com/danpozmanter/waftty"

[Setup]
AppId={{0E02FB8C-BC72-40BF-8039-4DFC60BDC21F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=waftty contributors
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AlwaysShowDirOnReadyPage=yes
PrivilegesRequiredOverridesAllowed=dialog
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile={#LicenseFile}
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#AppName}.ico
UninstallFilesDir={app}
ChangesEnvironment=yes
; A portable extraction leaves nothing to uninstall: deleting the folder
; removes waftty and its settings.
Uninstallable=not WizardIsTaskSelected('portablemode')

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "envpath"; Description: "Add waftty to PATH"; Flags: unchecked
Name: "portablemode"; Description: "Extract only, keeping settings in the folder (portable mode)"; Flags: unchecked

[Files]
Source: "{#Payload}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "{#IconFile}"; DestDir: "{app}"; DestName: "{#AppName}.ico"; Flags: ignoreversion

[Dirs]
Name: "{app}\user"; Tasks: portablemode

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppName}.ico"; Check: not WizardIsTaskSelected('portablemode')
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppName}.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  SystemEnvironment = 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';
  UserEnvironment = 'Environment';

{ An all-users install edits the system PATH, a per-user one the user's. }
function EnvironmentKey(var Root: Integer): String;
begin
  if IsAdminInstallMode then begin
    Root := HKEY_LOCAL_MACHINE;
    Result := SystemEnvironment;
  end else begin
    Root := HKEY_CURRENT_USER;
    Result := UserEnvironment;
  end;
end;

procedure AddToPath(Dir: String);
var
  Root: Integer;
  Key, Path: String;
begin
  Key := EnvironmentKey(Root);
  if not RegQueryStringValue(Root, Key, 'Path', Path) then
    Path := '';
  if Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Path) + ';') > 0 then
    Exit;
  if (Path <> '') and (Path[Length(Path)] <> ';') then
    Path := Path + ';';
  RegWriteExpandStringValue(Root, Key, 'Path', Path + Dir);
end;

procedure RemoveFromPath(Dir: String);
var
  Root, At: Integer;
  Key, Path: String;
begin
  Key := EnvironmentKey(Root);
  if not RegQueryStringValue(Root, Key, 'Path', Path) then
    Exit;
  Path := ';' + Path + ';';
  At := Pos(';' + Uppercase(Dir) + ';', Uppercase(Path));
  if At = 0 then
    Exit;
  Delete(Path, At, Length(Dir) + 1);
  RegWriteExpandStringValue(Root, Key, 'Path', Copy(Path, 2, Length(Path) - 2));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('envpath') then
    AddToPath(ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}'));
end;
